import os
import tempfile
import unittest
from pathlib import Path

from providers import get_provider
from providers.msfvenom import MsfvenomProvider


class MsfvenomProviderTests(unittest.TestCase):

    def _fake_msfvenom(
        self,
        directory: Path
    ):
        fake = directory / "fake-msfvenom"

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

output.write_bytes(
    b"MIFA-MSFVENOM-TEST"
)

sys.exit(0)
"""
        )

        fake.chmod(0o755)

        return fake

    def test_registry_returns_msfvenom_provider(
        self
    ):
        provider = get_provider(
            "msfvenom"
        )

        self.assertIsInstance(
            provider,
            MsfvenomProvider,
        )

    def test_missing_binary_rejected(
        self
    ):
        with self.assertRaises(
            FileNotFoundError
        ):
            MsfvenomProvider().resolve(
                "windows/x64/test",
                binary=(
                    "definitely-not-a-real-"
                    "msfvenom-binary"
                ),
            )

    def test_invalid_format_rejected(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            fake = self._fake_msfvenom(
                root
            )

            with self.assertRaises(
                ValueError
            ):
                MsfvenomProvider().resolve(
                    "windows/x64/test",
                    binary=str(fake),
                    format="invalid",
                    output_dir=root,
                )

    def test_generates_artifact(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            fake = self._fake_msfvenom(
                root
            )

            result = (
                MsfvenomProvider()
                .resolve(
                    "windows/x64/test",
                    binary=str(fake),
                    format="raw",
                    architecture="x64",
                    output_dir=root,
                    msf_options=[
                        "OPTION=value",
                    ],
                )
            )

            self.assertEqual(
                result["provider"],
                "msfvenom",
            )

            self.assertTrue(
                result["path"].exists()
            )

            self.assertEqual(
                result["path"].read_bytes(),
                b"MIFA-MSFVENOM-TEST",
            )

            provenance = (
                result["provenance"]
            )

            self.assertEqual(
                provenance["producer"],
                "msfvenom",
            )

            self.assertEqual(
                provenance["format"],
                "raw",
            )

            self.assertEqual(
                provenance["architecture"],
                "x64",
            )


if __name__ == "__main__":
    unittest.main()
