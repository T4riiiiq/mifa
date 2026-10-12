import tempfile
import unittest
from pathlib import Path

from core.payloads import PayloadManager


def make_pe(
    path,
    machine,
    dll=True
):
    is_x64 = (
        machine == 0x8664
    )

    optional_size = (
        0xF0
        if is_x64
        else 0xE0
    )

    optional_magic = (
        0x20B
        if is_x64
        else 0x10B
    )

    data = bytearray(
        0x200
    )

    data[0:2] = b"MZ"

    data[
        0x3C:0x40
    ] = (
        0x80
    ).to_bytes(
        4,
        "little"
    )

    data[
        0x80:0x84
    ] = bytes([0x50, 0x45, 0x00, 0x00])

    file_header = 0x84

    data[
        file_header:
        file_header + 2
    ] = machine.to_bytes(
        2,
        "little"
    )

    # No sections are needed for these
    # basic architecture/DLL fixtures.
    data[
        file_header + 2:
        file_header + 4
    ] = (
        0
    ).to_bytes(
        2,
        "little"
    )

    data[
        file_header + 16:
        file_header + 18
    ] = optional_size.to_bytes(
        2,
        "little"
    )

    characteristics = (
        0x2000
        if dll
        else 0x0002
    )

    data[
        file_header + 18:
        file_header + 20
    ] = characteristics.to_bytes(
        2,
        "little"
    )

    optional = (
        file_header + 20
    )

    data[
        optional:
        optional + 2
    ] = optional_magic.to_bytes(
        2,
        "little"
    )

    # SizeOfHeaders
    data[
        optional + 60:
        optional + 64
    ] = (
        0x200
    ).to_bytes(
        4,
        "little"
    )

    # NumberOfRvaAndSizes
    number_of_rva_offset = (
        optional + 108
        if is_x64
        else optional + 92
    )

    data[
        number_of_rva_offset:
        number_of_rva_offset + 4
    ] = (
        16
    ).to_bytes(
        4,
        "little"
    )

    Path(path).write_bytes(
        data
    )


class PEPayloadContractTests(
    unittest.TestCase
):
    def setUp(self):
        self.method = {
            "id":
                "dll-input",

            "requires_payload":
                True,

            "payload_types": [
                "pe"
            ],

            "payload_contract": {
                "required":
                    True,

                "types": [
                    "pe"
                ],

                "transforms": [
                    "copy"
                ],

                "default_transform":
                    "copy",

                "min_size_bytes":
                    1,

                "max_size_bytes":
                    10485760,

                "pe_kind":
                    "dll",
            },
        }

    def test_accepts_matching_x64_dll(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            payload = root / "demo.dll"
            build = root / "build"

            make_pe(
                payload,
                0x8664,
                dll=True,
            )

            result = (
                PayloadManager()
                .prepare(
                    payload_path=payload,
                    build_dir=build,
                    method=self.method,
                    payload_type="pe",
                    architecture="x64",
                )
            )

            self.assertTrue(
                result["pe"]["is_dll"]
            )

            self.assertEqual(
                result["pe"]["architecture"],
                "x64",
            )

    def test_rejects_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            payload = root / "demo.exe"

            make_pe(
                payload,
                0x8664,
                dll=False,
            )

            with self.assertRaisesRegex(
                ValueError,
                "Payload must be a DLL",
            ):
                PayloadManager().prepare(
                    payload_path=payload,
                    build_dir=root / "build",
                    method=self.method,
                    payload_type="pe",
                    architecture="x64",
                )

    def test_rejects_architecture_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            payload = root / "demo.dll"

            make_pe(
                payload,
                0x014C,
                dll=True,
            )

            with self.assertRaisesRegex(
                ValueError,
                "does not match selected architecture",
            ):
                PayloadManager().prepare(
                    payload_path=payload,
                    build_dir=root / "build",
                    method=self.method,
                    payload_type="pe",
                    architecture="x64",
                )


if __name__ == "__main__":
    unittest.main()
