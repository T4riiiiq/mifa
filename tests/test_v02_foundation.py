import json
import tempfile
import unittest
from pathlib import Path

from core.reporting import ReportExporter
from core.techniques import TechniqueRegistry
from providers import get_provider
from providers.external import ExternalProvider


ROOT = Path(
    __file__
).resolve().parents[1]


class V02FoundationTests(unittest.TestCase):
    def test_external_provider_registered(self):
        provider = get_provider(
            "external"
        )

        self.assertIsInstance(
            provider,
            ExternalProvider,
        )

    def test_external_provider_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = (
                Path(tmp)
                / "artifact.bin"
            )

            source.write_bytes(
                b"MIFA"
            )

            result = (
                ExternalProvider()
                .resolve(
                    source,
                    producer="tool-a",
                )
            )

            self.assertEqual(
                result["provenance"][
                    "provider"
                ],
                "external",
            )

            self.assertEqual(
                result["provenance"][
                    "producer"
                ],
                "tool-a",
            )

    def test_hidden_method_not_in_normal_discovery(self):
        registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        aliases = {
            method[
                "operational"
            ][
                "alias"
            ]
            for method
            in registry.discover()
        }

        self.assertNotIn(
            "package",
            aliases,
        )

    def test_hidden_method_available_in_all_discovery(self):
        registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        aliases = {
            method[
                "operational"
            ][
                "alias"
            ]
            for method
            in registry.discover(
                include_hidden=True
            )
        }

        self.assertIn(
            "package",
            aliases,
        )

    def test_report_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            build_dir = (
                root
                / "builds"
                / "K-0001"
            )

            build_dir.mkdir(
                parents=True
            )

            manifest = {
                "build_id": "K-0001",
                "status": "success",
                "created_at": "2026-01-01T00:00:00+00:00",
                "completed_at": "2026-01-01T00:00:01+00:00",
                "method": {
                    "id": "demo",
                    "name": "Demo",
                    "language": "cpp"
                },
                "preset": {
                    "architecture": "x64",
                    "build_type": "release"
                },
                "payload": {
                    "provider": {
                        "provider": "external",
                        "producer": "tool-a"
                    },
                    "type": "raw",
                    "transform": "copy",
                    "source": {
                        "name": "payload.bin",
                        "size_bytes": 4,
                        "sha256": "a" * 64
                    },
                    "staged": {
                        "file": "input/payload.bin",
                        "sha256": "a" * 64
                    }
                },
                "compiler": {
                    "name": "g++",
                    "command": [
                        "g++",
                        "main.cpp",
                        "-o",
                        "demo.exe"
                    ]
                },
                "output": {
                    "file": "output/demo.exe",
                    "size_bytes": 100,
                    "sha256": "b" * 64
                }
            }

            (
                build_dir
                / "build.json"
            ).write_text(
                json.dumps(
                    manifest
                ),
                encoding="utf-8"
            )

            exporter = ReportExporter(
                root
            )

            paths = exporter.export(
                "K-0001"
            )

            self.assertTrue(
                paths[
                    "build"
                ].exists()
            )

            text = paths[
                "report"
            ].read_text(
                encoding="utf-8"
            )

            self.assertIn(
                "Mifa Build Report",
                text,
            )

            self.assertIn(
                "tool-a",
                text,
            )

            self.assertIn(
                "K-0001",
                text,
            )


if __name__ == "__main__":
    unittest.main()
