import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from core.preflight import BuildPreflight


class PreflightTests(
    unittest.TestCase
):
    def create_pe(
        self,
        path,
        machine
    ):
        data = bytearray(
            0x100
        )

        data[0:2] = b"MZ"

        struct.pack_into(
            "<I",
            data,
            0x3C,
            0x80,
        )

        data[
            0x80:
            0x84
        ] = b"PE\x00\x00"

        struct.pack_into(
            "<H",
            data,
            0x84,
            machine,
        )

        path.write_bytes(
            data
        )

    def create_manifest(
        self,
        root,
        machine,
        expected_arch
    ):
        build_dir = (
            root
            / "builds"
            / "K-0001"
        )

        output_dir = (
            build_dir
            / "output"
        )

        output_dir.mkdir(
            parents=True
        )

        artifact = (
            output_dir
            / "demo.exe"
        )

        self.create_pe(
            artifact,
            machine,
        )

        sha256 = hashlib.sha256(
            artifact.read_bytes()
        ).hexdigest()

        manifest = {
            "build_id":
                "K-0001",

            "status":
                "success",

            "preset": {
                "architecture":
                    expected_arch,
            },

            "payload": {
                "pipeline": {
                    "roundtrip_match":
                        True,
                },
            },

            "output": {
                "file":
                    "output/demo.exe",

                "sha256":
                    sha256,
            },
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

    def test_preflight_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.create_manifest(
                root,
                0x8664,
                "x64",
            )

            result = BuildPreflight(
                root
            ).verify(
                "K-0001"
            )

            self.assertEqual(
                result["result"],
                "PASS",
            )

            self.assertTrue(
                result[
                    "hash_match"
                ]
            )

            self.assertTrue(
                result[
                    "arch_match"
                ]
            )

    def test_architecture_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.create_manifest(
                root,
                0x014C,
                "x64",
            )

            result = BuildPreflight(
                root
            ).verify(
                "K-0001"
            )

            self.assertEqual(
                result["result"],
                "FAIL",
            )

            self.assertFalse(
                result[
                    "arch_match"
                ]
            )


if __name__ == "__main__":
    unittest.main()
