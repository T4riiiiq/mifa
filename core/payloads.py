from pathlib import Path
import base64
import binascii
import hashlib
import json
import mimetypes
import shutil


class PayloadManager:
    SUPPORTED_TYPES = {
        "raw",
        "text",
        "json",
        "pe"
    }

    SUPPORTED_TRANSFORMS = {
        "copy",
        "base64",
        "hex"
    }

    DEFAULT_MAX_SIZE_BYTES = (
        64 * 1024 * 1024
    )

    def _sha256(
        self,
        path: Path
    ):
        digest = hashlib.sha256()

        with path.open(
            "rb"
        ) as f:
            while True:
                chunk = f.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(
                    chunk
                )

        return digest.hexdigest()

    def _contract(
        self,
        method
    ):
        contract = method.get(
            "payload_contract"
        )

        if contract is None:
            return {
                "required":
                    method.get(
                        "requires_payload",
                        False
                    ),

                "types":
                    list(
                        method.get(
                            "payload_types",
                            []
                        )
                    ),

                "transforms": [
                    "copy"
                ],

                "default_transform":
                    "copy",

                "min_size_bytes":
                    1,

                "max_size_bytes":
                    self.DEFAULT_MAX_SIZE_BYTES
            }

        return {
            "required":
                contract.get(
                    "required",
                    method.get(
                        "requires_payload",
                        False
                    )
                ),

            "types":
                list(
                    contract.get(
                        "types",
                        method.get(
                            "payload_types",
                            []
                        )
                    )
                ),

            "transforms":
                list(
                    contract.get(
                        "transforms",
                        [
                            "copy"
                        ]
                    )
                ),

            "default_transform":
                contract.get(
                    "default_transform",
                    "copy"
                ),

            "min_size_bytes":
                contract.get(
                    "min_size_bytes",
                    1
                ),

            "max_size_bytes":
                contract.get(
                    "max_size_bytes",
                    self.DEFAULT_MAX_SIZE_BYTES
                )
        }

    def _validate_type(
        self,
        payload_path: Path,
        payload_type
    ):
        if payload_type == "raw":
            return

        data = payload_path.read_bytes()

        if payload_type == "text":
            try:
                data.decode(
                    "utf-8"
                )

            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Payload type 'text' requires "
                    "valid UTF-8 input"
                ) from exc

            return

        if payload_type == "json":
            try:
                json.loads(
                    data.decode(
                        "utf-8"
                    )
                )

            except (
                UnicodeDecodeError,
                json.JSONDecodeError
            ) as exc:
                raise ValueError(
                    "Payload type 'json' requires "
                    "valid UTF-8 JSON input"
                ) from exc

            return

        if payload_type == "pe":
            if (
                len(data) < 2
                or data[:2] != b"MZ"
            ):
                raise ValueError(
                    "Payload type 'pe' requires "
                    "a file beginning with the "
                    "MZ signature"
                )

            return

        raise ValueError(
            f"Unsupported payload type: "
            f"{payload_type}"
        )

    def _transform_name(
        self,
        source_name,
        transform
    ):
        if transform == "copy":
            return source_name

        if transform == "base64":
            return (
                source_name
                + ".b64"
            )

        if transform == "hex":
            return (
                source_name
                + ".hex"
            )

        raise ValueError(
            f"Unsupported payload transform: "
            f"{transform}"
        )

    def _write_transformed(
        self,
        source: Path,
        destination: Path,
        transform
    ):
        if transform == "copy":
            shutil.copy2(
                source,
                destination
            )
            return

        data = source.read_bytes()

        if transform == "base64":
            destination.write_bytes(
                base64.b64encode(
                    data
                )
            )
            return

        if transform == "hex":
            destination.write_bytes(
                binascii.hexlify(
                    data
                )
            )
            return

        raise ValueError(
            f"Unsupported payload transform: "
            f"{transform}"
        )

    def prepare(
        self,
        payload_path: Path,
        build_dir: Path,
        method,
        payload_type,
        transform=None
    ):
        payload_path = (
            payload_path
            .expanduser()
            .resolve()
        )

        if not payload_path.exists():
            raise FileNotFoundError(
                f"Payload not found: "
                f"{payload_path}"
            )

        if not payload_path.is_file():
            raise ValueError(
                f"Payload is not a file: "
                f"{payload_path}"
            )

        contract = self._contract(
            method
        )

        if payload_type not in (
            contract[
                "types"
            ]
        ):
            raise ValueError(
                f"Payload type "
                f"'{payload_type}' is not "
                f"accepted by method "
                f"'{method.get('id')}'"
            )

        if (
            payload_type
            not in self.SUPPORTED_TYPES
        ):
            raise ValueError(
                f"Unsupported payload type: "
                f"{payload_type}"
            )

        source_size = (
            payload_path
            .stat()
            .st_size
        )

        minimum = contract.get(
            "min_size_bytes",
            1
        )

        maximum = contract.get(
            "max_size_bytes",
            self.DEFAULT_MAX_SIZE_BYTES
        )

        if source_size < minimum:
            raise ValueError(
                f"Payload size "
                f"{source_size} bytes is below "
                f"the minimum of {minimum}"
            )

        if source_size > maximum:
            raise ValueError(
                f"Payload size "
                f"{source_size} bytes exceeds "
                f"the maximum of {maximum}"
            )

        self._validate_type(
            payload_path,
            payload_type
        )

        selected_transform = (
            transform
            or contract.get(
                "default_transform",
                "copy"
            )
        )

        if selected_transform not in (
            contract[
                "transforms"
            ]
        ):
            raise ValueError(
                f"Payload transform "
                f"'{selected_transform}' is not "
                f"accepted by method "
                f"'{method.get('id')}'"
            )

        if (
            selected_transform
            not in self.SUPPORTED_TRANSFORMS
        ):
            raise ValueError(
                f"Unsupported payload transform: "
                f"{selected_transform}"
            )

        input_dir = (
            build_dir / "input"
        )

        input_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        staged_name = (
            self._transform_name(
                payload_path.name,
                selected_transform
            )
        )

        destination = (
            input_dir
            / staged_name
        )

        self._write_transformed(
            source=payload_path,
            destination=destination,
            transform=selected_transform
        )

        source_sha256 = (
            self._sha256(
                payload_path
            )
        )

        staged_sha256 = (
            self._sha256(
                destination
            )
        )

        staged_size = (
            destination
            .stat()
            .st_size
        )

        mime_type, _ = (
            mimetypes.guess_type(
                payload_path.name
            )
        )

        source = {
            "name":
                payload_path.name,

            "suffix":
                payload_path.suffix.lower(),

            "mime_type":
                mime_type,

            "size_bytes":
                source_size,

            "sha256":
                source_sha256
        }

        staged = {
            "file":
                str(
                    destination.relative_to(
                        build_dir
                    )
                ),

            "name":
                destination.name,

            "size_bytes":
                staged_size,

            "sha256":
                staged_sha256
        }

        return {
            "original":
                str(
                    payload_path
                ),

            "type":
                payload_type,

            "transform":
                selected_transform,

            "source":
                source,

            "staged":
                staged,

            # Backward-compatible staged fields.
            "file":
                staged[
                    "file"
                ],

            "name":
                staged[
                    "name"
                ],

            "size_bytes":
                staged[
                    "size_bytes"
                ],

            "sha256":
                staged[
                    "sha256"
                ]
        }
