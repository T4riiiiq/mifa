import tempfile
import unittest
from pathlib import Path

from core.pe import inspect_pe


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


class PETests(
    unittest.TestCase
):
    def test_x64_dll(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = (
                Path(tmp)
                / "x64.dll"
            )

            make_pe(
                path,
                0x8664,
            )

            result = inspect_pe(
                path
            )

            self.assertEqual(
                result[
                    "architecture"
                ],
                "x64",
            )

            self.assertTrue(
                result[
                    "is_dll"
                ]
            )

    def test_x86_dll(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = (
                Path(tmp)
                / "x86.dll"
            )

            make_pe(
                path,
                0x014C,
            )

            result = inspect_pe(
                path
            )

            self.assertEqual(
                result[
                    "architecture"
                ],
                "x86",
            )

            self.assertTrue(
                result[
                    "is_dll"
                ]
            )

    def test_exe_is_not_dll(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = (
                Path(tmp)
                / "app.exe"
            )

            make_pe(
                path,
                0x8664,
                dll=False,
            )

            result = inspect_pe(
                path
            )

            self.assertFalse(
                result[
                    "is_dll"
                ]
            )


if __name__ == "__main__":
    unittest.main()

class PEExportTests(unittest.TestCase):
    def test_reads_export_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = (
                Path(tmp)
                / "reflective.dll"
            )

            data = bytearray(
                0x400
            )

            data[0:2] = b"MZ"
            data[0x3C:0x40] = (
                0x80
            ).to_bytes(
                4,
                "little"
            )

            data[0x80:0x84] = (
                b"PE\x00\x00"
            )

            file_header = 0x84

            data[
                file_header:
                file_header + 2
            ] = (
                0x8664
            ).to_bytes(
                2,
                "little"
            )

            data[
                file_header + 2:
                file_header + 4
            ] = (
                1
            ).to_bytes(
                2,
                "little"
            )

            data[
                file_header + 16:
                file_header + 18
            ] = (
                0xF0
            ).to_bytes(
                2,
                "little"
            )

            data[
                file_header + 18:
                file_header + 20
            ] = (
                0x2000
            ).to_bytes(
                2,
                "little"
            )

            optional = (
                file_header + 20
            )

            data[
                optional:
                optional + 2
            ] = (
                0x20B
            ).to_bytes(
                2,
                "little"
            )

            data[
                optional + 60:
                optional + 64
            ] = (
                0x200
            ).to_bytes(
                4,
                "little"
            )

            data[
                optional + 108:
                optional + 112
            ] = (
                16
            ).to_bytes(
                4,
                "little"
            )

            data[
                optional + 112:
                optional + 116
            ] = (
                0x1000
            ).to_bytes(
                4,
                "little"
            )

            section = (
                optional + 0xF0
            )

            data[
                section + 8:
                section + 12
            ] = (
                0x200
            ).to_bytes(
                4,
                "little"
            )

            data[
                section + 12:
                section + 16
            ] = (
                0x1000
            ).to_bytes(
                4,
                "little"
            )

            data[
                section + 16:
                section + 20
            ] = (
                0x200
            ).to_bytes(
                4,
                "little"
            )

            data[
                section + 20:
                section + 24
            ] = (
                0x200
            ).to_bytes(
                4,
                "little"
            )

            export = 0x200

            data[
                export + 24:
                export + 28
            ] = (
                1
            ).to_bytes(
                4,
                "little"
            )

            data[
                export + 32:
                export + 36
            ] = (
                0x1040
            ).to_bytes(
                4,
                "little"
            )

            data[
                0x240:0x244
            ] = (
                0x1050
            ).to_bytes(
                4,
                "little"
            )

            name = (
                b"ReflectiveLoader\x00"
            )

            data[
                0x250:
                0x250 + len(name)
            ] = name

            path.write_bytes(
                data
            )

            result = inspect_pe(
                path
            )

            self.assertIn(
                "ReflectiveLoader",
                result["exports"],
            )
