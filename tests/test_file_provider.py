import json
import tempfile
import unittest
from pathlib import Path

from core.builds import BuildManager
from core.payloads import PayloadManager
from providers import get_provider
from providers.file import FileProvider


class FileProviderTests(unittest.TestCase):
    def test_registry_returns_file_provider(self):
        provider = get_provider(
            "file"
        )

        self.assertIsInstance(
            provider,
            FileProvider,
        )

    def test_unknown_provider_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            get_provider(
                "missing"
            )

    def test_file_provider_resolves_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / "payload.bin"
            payload.write_bytes(
                b"MIFA"
            )

            result = FileProvider().resolve(
                payload
            )

            self.assertEqual(
                result["provider"],
                "file",
            )

            self.assertEqual(
                result["path"],
                payload.resolve(),
            )

            self.assertEqual(
                result["provenance"][
                    "source_name"
                ],
                "payload.bin",
            )

    def test_file_provider_rejects_missing_file(self):
        with self.assertRaises(
            FileNotFoundError
        ):
            FileProvider().resolve(
                "/definitely/missing/mifa.bin"
            )

    def test_provider_to_payload_pipeline(self):
        method = {
            "id": "demo",
            "requires_payload": True,
            "payload_types": [
                "raw",
            ],
            "payload_contract": {
                "required": True,
                "types": [
                    "raw",
                ],
                "transforms": [
                    "copy",
                ],
                "default_transform": "copy",
                "min_size_bytes": 1,
                "max_size_bytes": 1024,
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            source = (
                root
                / "payload.bin"
            )

            source.write_bytes(
                b"MIFA"
            )

            build_dir = (
                root
                / "build"
            )

            provider_result = (
                FileProvider().resolve(
                    source
                )
            )

            payload_info = (
                PayloadManager().prepare(
                    payload_path=provider_result[
                        "path"
                    ],
                    build_dir=build_dir,
                    method=method,
                    payload_type="raw",
                    transform="copy",
                )
            )

            self.assertEqual(
                payload_info["source"][
                    "sha256"
                ],
                payload_info["staged"][
                    "sha256"
                ],
            )

    def test_manifest_records_provider(self):
        method = {
            "id": "demo",
            "name": "Demo",
            "language": "cpp",
            "runtime_arguments": [],
            "payload_contract": {
                "required": True,
            },
        }

        preset = {
            "id": "demo-x64",
            "architecture": "x64",
            "build_type": "release",
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            manager = BuildManager(
                root / "builds"
            )

            _, build_dir = manager.create(
                method=method,
                preset=preset,
            )

            payload_info = {
                "transform": "copy",
                "source": {
                    "name": "payload.bin",
                    "size_bytes": 4,
                    "sha256": "a" * 64,
                },
                "staged": {
                    "file": "input/payload.bin",
                    "name": "payload.bin",
                    "size_bytes": 4,
                    "sha256": "a" * 64,
                },
                "file": "input/payload.bin",
                "name": "payload.bin",
                "size_bytes": 4,
                "sha256": "a" * 64,
            }

            provider = {
                "provider": "file",
                "source_name": "payload.bin",
                "source_path": "/tmp/payload.bin",
            }

            manager.attach_payload(
                build_dir=build_dir,
                payload_info=payload_info,
                payload_type="raw",
                provider_info=provider,
            )

            data = json.loads(
                (
                    build_dir
                    / "build.json"
                ).read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                data["payload"][
                    "provider"
                ][
                    "provider"
                ],
                "file",
            )


if __name__ == "__main__":
    unittest.main()
