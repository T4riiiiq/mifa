from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re


class BuildManager:
    def __init__(
        self,
        builds_dir: Path
    ):
        self.builds_dir = builds_dir

        self.builds_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def _now(self):
        return datetime.now(
            timezone.utc
        ).isoformat()

    def _next_build_id(self):
        pattern = re.compile(
            r"^K-(\d{4})$"
        )

        highest = 0

        for path in self.builds_dir.iterdir():
            if not path.is_dir():
                continue

            match = pattern.match(
                path.name
            )

            if match:
                highest = max(
                    highest,
                    int(
                        match.group(1)
                    )
                )

        return (
            f"K-{highest + 1:04d}"
        )

    def _manifest_path(
        self,
        build_dir: Path
    ):
        return (
            build_dir
            / "build.json"
        )

    def _read_manifest(
        self,
        build_dir: Path
    ):
        path = self._manifest_path(
            build_dir
        )

        with path.open(
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(
                f
            )

    def _write_manifest(
        self,
        build_dir: Path,
        data
    ):
        path = self._manifest_path(
            build_dir
        )

        with path.open(
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=4
            )

    def _sha256(
        self,
        file_path: Path
    ):
        digest = hashlib.sha256()

        with file_path.open(
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

    def create(
        self,
        method,
        preset,
        parameters=None
    ):
        build_id = (
            self._next_build_id()
        )

        build_dir = (
            self.builds_dir
            / build_id
        )

        source_dir = (
            build_dir
            / "source"
        )

        output_dir = (
            build_dir
            / "output"
        )

        source_dir.mkdir(
            parents=True
        )

        output_dir.mkdir(
            parents=True
        )

        build_data = {
            "build_id":
                build_id,

            "created_at":
                self._now(),

            "completed_at":
                None,

            "status":
                "created",

            "method": {
                "id":
                    method.get(
                        "id"
                    ),

                "name":
                    method.get(
                        "name"
                    ),

                "language":
                    method.get(
                        "language"
                    )
            },

            "preset": {
                "id":
                    preset.get(
                        "id"
                    ),

                "architecture":
                    preset.get(
                        "architecture"
                    ),

                "build_type":
                    preset.get(
                        "build_type"
                    )
            },

            "parameters":
                parameters or {},

            "runtime_arguments":
                method.get(
                    "runtime_arguments",
                    []
                ),

            "payload_contract":
                method.get(
                    "payload_contract"
                ),

            "payload":
                None
        }

        self._write_manifest(
            build_dir,
            build_data
        )

        return (
            build_id,
            build_dir
        )

    def attach_payload(
        self,
        build_dir: Path,
        payload_info,
        payload_type
    ):
        data = self._read_manifest(
            build_dir
        )

        data["payload"] = {
            "type":
                payload_type,

            "transform":
                payload_info.get(
                    "transform",
                    "copy"
                ),

            "source":
                payload_info.get(
                    "source"
                ),

            "staged":
                payload_info.get(
                    "staged"
                ),

            # Backward-compatible staged fields.
            "file":
                payload_info[
                    "file"
                ],

            "name":
                payload_info[
                    "name"
                ],

            "size_bytes":
                payload_info[
                    "size_bytes"
                ],

            "sha256":
                payload_info[
                    "sha256"
                ]
        }

        self._write_manifest(
            build_dir,
            data
        )

    def mark_success(
        self,
        build_dir: Path,
        generated_files,
        compile_result
    ):
        data = self._read_manifest(
            build_dir
        )

        output_path = Path(
            compile_result[
                "output"
            ]
        )

        data["status"] = (
            "success"
        )

        data["completed_at"] = (
            self._now()
        )

        data["sources"] = []

        for item in generated_files:
            source_path = Path(
                item["path"]
            )

            data["sources"].append({
                "file":
                    str(
                        source_path.relative_to(
                            build_dir
                        )
                    ),

                "compile":
                    item[
                        "compile"
                    ]
            })

        data["compiler"] = {
            "name":
                compile_result[
                    "compiler"
                ],

            "command":
                compile_result[
                    "command"
                ]
        }

        data["output"] = {
            "file":
                str(
                    output_path.relative_to(
                        build_dir
                    )
                ),

            "size_bytes":
                output_path.stat().st_size,

            "sha256":
                self._sha256(
                    output_path
                )
        }

        self._write_manifest(
            build_dir,
            data
        )

        return data

    def mark_failed(
        self,
        build_dir: Path,
        error
    ):
        data = self._read_manifest(
            build_dir
        )

        data["status"] = (
            "failed"
        )

        data["completed_at"] = (
            self._now()
        )

        data["error"] = str(
            error
        )

        self._write_manifest(
            build_dir,
            data
        )
