import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MsfvenomCliTests(unittest.TestCase):

    def _cleanup_test_outputs(
        self,
        before_builds,
        before_reports
    ):
        builds_dir = ROOT / "builds"
        reports_dir = ROOT / "reports"

        for item in builds_dir.glob("K-*"):
            if (
                item.name not in before_builds
                and item.is_dir()
            ):
                shutil.rmtree(
                    item,
                    ignore_errors=True
                )

        for item in reports_dir.glob("K-*.md"):
            if item.name not in before_reports:
                item.unlink(
                    missing_ok=True
                )

    def _fake_msfvenom(
        self,
        directory: Path
    ):
        fake = directory / "msfvenom"

        fake.write_text(
            """#!/usr/bin/env python3
import pathlib
import sys

args = sys.argv[1:]

if "-o" not in args:
    sys.exit(2)

output = pathlib.Path(
    args[args.index("-o") + 1]
)

# Benign x64 fixture:
# mov eax, 0x1234
# ret
output.write_bytes(
    bytes.fromhex("B834120000C3")
)

sys.exit(0)
"""
        )

        fake.chmod(0o755)

        return fake

    def test_payloads_lists_msfvenom(
        self
    ):
        completed = subprocess.run(
            [
                sys.executable,
                "mifa.py",
                "payloads",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr,
        )

        self.assertIn(
            "msfvenom",
            completed.stdout.splitlines(),
        )

    def test_cli_build_with_msfvenom_provider(
        self
    ):
        before_builds = {
            item.name
            for item in (
                ROOT / "builds"
            ).glob("K-*")
        }

        before_reports = {
            item.name
            for item in (
                ROOT / "reports"
            ).glob("K-*.md")
        }

        self.addCleanup(
            self._cleanup_test_outputs,
            before_builds,
            before_reports,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()

            self._fake_msfvenom(
                fake_bin
            )

            env = os.environ.copy()

            env["PATH"] = (
                str(fake_bin)
                + os.pathsep
                + env.get(
                    "PATH",
                    ""
                )
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "mifa.py",
                    "--verbose",
                    "build",

                    "--technique",
                    "remote-thread",

                    "--payload",
                    "test/benign-x64",

                    "--provider",
                    "msfvenom",

                    "--payload-type",
                    "raw",

                    "--arch",
                    "x64",

                    "--build-type",
                    "release",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout
                + completed.stderr,
            )

            self.assertIn(
                "Preflight passed",
                completed.stdout,
            )

            match = re.search(
                r"^\s*Manifest\s*:\s*(.+)$",
                completed.stdout,
                re.MULTILINE,
            )

            self.assertIsNotNone(
                match,
                completed.stdout,
            )

            manifest_path = Path(
                match.group(1).strip()
            )

            self.assertTrue(
                manifest_path.exists()
            )

            data = json.loads(
                manifest_path.read_text()
            )

            provider = (
                data["payload"]["provider"]
            )

            self.assertEqual(
                provider["provider"],
                "msfvenom",
            )

            self.assertEqual(
                provider["producer"],
                "msfvenom",
            )

            self.assertEqual(
                provider["payload"],
                "test/benign-x64",
            )

            self.assertEqual(
                provider["format"],
                "raw",
            )

            self.assertEqual(
                provider["architecture"],
                "x64",
            )

            self.assertEqual(
                provider["platform"],
                "windows",
            )


if __name__ == "__main__":
    unittest.main()
