from pathlib import Path
import hashlib
import json
import mimetypes
import shutil

from core.pe import inspect_pe


class PayloadManager:
    SUPPORTED_TYPES = {
        "raw",
        "text",
        "json",
        "pe",
    }

    SUPPORTED_TRANSFORMS = {
        "copy",
    }

    DEFAULT_MAX_SIZE_BYTES = 64 * 1024 * 1024

    def _sha256(self, path: Path):
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    def _contract(self, method):
        contract = method.get("payload_contract")

        if contract is None:
            return {
                "required": method.get("requires_payload", False),
                "types": list(method.get("payload_types", [])),
                "transforms": ["copy"],
                "default_transform": "copy",
                "min_size_bytes": 1,
                "max_size_bytes": self.DEFAULT_MAX_SIZE_BYTES,
                "pe_kind": None,
                "required_exports": [],
            }

        return {
            "required": contract.get(
                "required",
                method.get("requires_payload", False),
            ),
            "types": list(
                contract.get(
                    "types",
                    method.get("payload_types", []),
                )
            ),
            "transforms": list(
                contract.get(
                    "transforms",
                    ["copy"],
                )
            ),
            "default_transform": contract.get(
                "default_transform",
                "copy",
            ),
            "min_size_bytes": contract.get(
                "min_size_bytes",
                1,
            ),
            "max_size_bytes": contract.get(
                "max_size_bytes",
                self.DEFAULT_MAX_SIZE_BYTES,
            ),
            "pe_kind": contract.get("pe_kind"),
            "required_exports": list(
                contract.get(
                    "required_exports",
                    [],
                )
            ),
        }

    def _validate_type(
        self,
        payload_path: Path,
        payload_type,
    ):
        if payload_type == "raw":
            return

        data = payload_path.read_bytes()

        if payload_type == "text":
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Payload type 'text' requires valid UTF-8 input"
                ) from exc
            return

        if payload_type == "json":
            try:
                json.loads(data.decode("utf-8"))
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ) as exc:
                raise ValueError(
                    "Payload type 'json' requires valid UTF-8 JSON input"
                ) from exc
            return

        if payload_type == "pe":
            if len(data) < 2 or data[:2] != b"MZ":
                raise ValueError(
                    "Payload type 'pe' requires a file beginning with the MZ signature"
                )
            return

        raise ValueError(
            f"Unsupported payload type: {payload_type}"
        )

    def prepare(
        self,
        payload_path: Path,
        build_dir: Path,
        method,
        payload_type,
        transform=None,
        architecture=None,
    ):
        payload_path = payload_path.expanduser().resolve()

        if not payload_path.exists():
            raise FileNotFoundError(
                f"Payload not found: {payload_path}"
            )

        if not payload_path.is_file():
            raise ValueError(
                f"Payload is not a file: {payload_path}"
            )

        contract = self._contract(method)

        if payload_type not in contract["types"]:
            raise ValueError(
                f"Payload type '{payload_type}' is not accepted by method "
                f"'{method.get('id')}'"
            )

        if payload_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported payload type: {payload_type}"
            )

        source_size = payload_path.stat().st_size
        minimum = contract.get("min_size_bytes", 1)
        maximum = contract.get(
            "max_size_bytes",
            self.DEFAULT_MAX_SIZE_BYTES,
        )

        if source_size < minimum:
            raise ValueError(
                f"Payload size {source_size} bytes is below the minimum of {minimum}"
            )

        if source_size > maximum:
            raise ValueError(
                f"Payload size {source_size} bytes exceeds the maximum of {maximum}"
            )

        self._validate_type(
            payload_path,
            payload_type,
        )

        pe_info = None

        if payload_type == "pe":
            pe_info = inspect_pe(payload_path)

            pe_kind = contract.get("pe_kind")

            if pe_kind == "dll" and not pe_info["is_dll"]:
                raise ValueError("Payload must be a DLL")

            if pe_kind == "exe" and pe_info["is_dll"]:
                raise ValueError("Payload must be an executable")

            if architecture and pe_info["architecture"] != architecture:
                raise ValueError(
                    f"PE architecture '{pe_info['architecture']}' "
                    f"does not match selected architecture '{architecture}'"
                )

            required_exports = contract.get(
                "required_exports",
                [],
            )

            missing_exports = [
                export
                for export in required_exports
                if export not in pe_info["exports"]
            ]

            if missing_exports:
                raise ValueError(
                    "Missing required PE export(s): "
                    + ", ".join(missing_exports)
                )

        selected_transform = (
            transform
            or contract.get(
                "default_transform",
                "copy",
            )
        )

        if selected_transform not in contract["transforms"]:
            raise ValueError(
                f"Payload transform '{selected_transform}' is not accepted "
                f"by method '{method.get('id')}'"
            )

        if selected_transform != "copy":
            raise ValueError(
                f"Unsupported payload transform: {selected_transform}"
            )

        input_dir = build_dir / "input"
        input_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = input_dir / payload_path.name

        shutil.copy2(
            payload_path,
            destination,
        )

        source_sha256 = self._sha256(payload_path)
        staged_sha256 = self._sha256(destination)
        staged_size = destination.stat().st_size
        mime_type, _ = mimetypes.guess_type(
            payload_path.name
        )

        source = {
            "name": payload_path.name,
            "suffix": payload_path.suffix.lower(),
            "mime_type": mime_type,
            "size_bytes": source_size,
            "sha256": source_sha256,
        }

        staged = {
            "file": str(
                destination.relative_to(build_dir)
            ),
            "name": destination.name,
            "size_bytes": staged_size,
            "sha256": staged_sha256,
        }

        return {
            "original": str(payload_path),
            "type": payload_type,
            "transform": "copy",
            "source": source,
            "staged": staged,
            "pe": pe_info,
            "file": staged["file"],
            "name": staged["name"],
            "size_bytes": staged["size_bytes"],
            "sha256": staged["sha256"],
        }
