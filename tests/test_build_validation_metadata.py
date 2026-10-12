import json
import tempfile
import unittest
from pathlib import Path

from core.builds import BuildManager


class BuildValidationMetadataTests(
    unittest.TestCase
):
    def test_manifest_records_validation_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            manager = BuildManager(
                root / "builds"
            )

            method = {
                "id": "demo",
                "name": "Demo",
                "language": "c",
                "operational": {
                    "alias": "demo",
                    "runtime": "native",
                    "validation": "build-tested",
                },
            }

            preset = {
                "id": "demo-x64-release",
                "architecture": "x64",
                "build_type": "release",
            }

            _, build_dir = manager.create(
                method=method,
                preset=preset,
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
                data["method"]["alias"],
                "demo",
            )

            self.assertEqual(
                data["method"]["runtime"],
                "native",
            )

            self.assertEqual(
                data["method"]["validation"],
                "build-tested",
            )


if __name__ == "__main__":
    unittest.main()
