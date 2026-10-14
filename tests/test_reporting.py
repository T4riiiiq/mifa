import json
import tempfile
import unittest
from pathlib import Path

from core.reporting import ReportExporter


class ReportingTests(unittest.TestCase):
    def test_msfvenom_options_are_reported_without_values(
        self
    ):
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
                "created_at": "2026-10-14T00:00:00Z",
                "completed_at": "2026-10-14T00:00:01Z",
                "method": {
                    "id": "remote-thread",
                    "name": "Remote Thread",
                    "language": "c",
                },
                "preset": {
                    "architecture": "x64",
                    "build_type": "release",
                },
                "payload": {
                    "type": "raw",
                    "transform": "copy",
                    "provider": {
                        "provider": "msfvenom",
                        "producer": "msfvenom",
                        "binary": "msfvenom",
                        "msf_option_keys": [
                            "LHOST",
                            "LPORT",
                        ],
                        "msf_option_values_redacted": True,
                        "ignored_secret": "super-secret",
                    },
                    "source": {
                        "name": "payload.bin",
                        "size_bytes": 10,
                        "sha256": "a" * 64,
                    },
                    "staged": {
                        "file": "input/payload.bin",
                        "sha256": "a" * 64,
                    },
                },
                "compiler": {
                    "name": "gcc",
                    "command": [
                        "gcc",
                        "main.c",
                    ],
                },
                "output": {
                    "file": "output/demo.exe",
                    "size_bytes": 123,
                    "sha256": "b" * 64,
                },
            }

            (
                build_dir
                / "build.json"
            ).write_text(
                json.dumps(
                    manifest
                ),
                encoding="utf-8",
            )

            report = ReportExporter(
                root
            ).render(
                "K-0001"
            )

            self.assertIn(
                "Generator binary: `msfvenom`",
                report,
            )

            self.assertIn(
                "Generator options: `LHOST, LPORT`",
                report,
            )

            self.assertIn(
                "Generator option values: `redacted`",
                report,
            )

            self.assertNotIn(
                "super-secret",
                report,
            )


if __name__ == "__main__":
    unittest.main()
