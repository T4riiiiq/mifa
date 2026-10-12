from pathlib import Path


IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_FILE_DLL = 0x2000

PE32_MAGIC = 0x10B
PE32_PLUS_MAGIC = 0x20B


def _u16(data, offset):
    if offset + 2 > len(data):
        raise ValueError("Unexpected end of PE file")

    return int.from_bytes(
        data[offset:offset + 2],
        "little",
    )


def _u32(data, offset):
    if offset + 4 > len(data):
        raise ValueError("Unexpected end of PE file")

    return int.from_bytes(
        data[offset:offset + 4],
        "little",
    )


def _read_c_string(
    data,
    offset,
    max_length=4096
):
    if offset >= len(data):
        raise ValueError(
            "String offset outside PE file"
        )

    end = data.find(
        b"\x00",
        offset,
        min(
            len(data),
            offset + max_length,
        ),
    )

    if end == -1:
        raise ValueError(
            "Unterminated PE string"
        )

    return data[
        offset:end
    ].decode(
        "ascii",
        errors="replace",
    )


def _rva_to_offset(
    data,
    rva,
    sections,
    size_of_headers
):
    if rva < size_of_headers:
        if rva >= len(data):
            raise ValueError(
                "RVA outside PE file"
            )

        return rva

    for section in sections:
        start = section[
            "virtual_address"
        ]

        span = max(
            section[
                "virtual_size"
            ],
            section[
                "raw_size"
            ],
        )

        if start <= rva < start + span:
            offset = (
                section[
                    "raw_offset"
                ]
                + (rva - start)
            )

            if offset >= len(data):
                raise ValueError(
                    "RVA maps outside PE file"
                )

            return offset

    raise ValueError(
        f"Unable to map RVA 0x{rva:x}"
    )


def _exports(
    data,
    export_rva,
    sections,
    size_of_headers
):
    if export_rva == 0:
        return []

    directory = _rva_to_offset(
        data,
        export_rva,
        sections,
        size_of_headers,
    )

    if directory + 40 > len(data):
        raise ValueError(
            "Invalid export directory"
        )

    number_of_names = _u32(
        data,
        directory + 24,
    )

    names_rva = _u32(
        data,
        directory + 32,
    )

    if (
        number_of_names == 0
        or names_rva == 0
    ):
        return []

    names_offset = _rva_to_offset(
        data,
        names_rva,
        sections,
        size_of_headers,
    )

    exports = []

    for index in range(
        number_of_names
    ):
        entry = (
            names_offset
            + (index * 4)
        )

        name_rva = _u32(
            data,
            entry,
        )

        name_offset = _rva_to_offset(
            data,
            name_rva,
            sections,
            size_of_headers,
        )

        exports.append(
            _read_c_string(
                data,
                name_offset,
            )
        )

    return sorted(
        set(exports)
    )


def inspect_pe(path):
    path = Path(path)
    data = path.read_bytes()

    if len(data) < 0x40:
        raise ValueError(
            "PE file is too small"
        )

    if data[:2] != b"MZ":
        raise ValueError(
            "Missing DOS MZ signature"
        )

    pe_offset = _u32(
        data,
        0x3C,
    )

    if pe_offset + 24 > len(data):
        raise ValueError(
            "Invalid PE header offset"
        )

    if (
        data[
            pe_offset:
            pe_offset + 4
        ]
        != b"PE\x00\x00"
    ):
        raise ValueError(
            "Missing PE signature"
        )

    file_header = pe_offset + 4

    machine = _u16(
        data,
        file_header,
    )

    number_of_sections = _u16(
        data,
        file_header + 2,
    )

    optional_size = _u16(
        data,
        file_header + 16,
    )

    characteristics = _u16(
        data,
        file_header + 18,
    )

    optional = (
        file_header + 20
    )

    if optional + optional_size > len(data):
        raise ValueError(
            "Invalid optional header"
        )

    magic = _u16(
        data,
        optional,
    )

    if magic == PE32_MAGIC:
        data_directory = (
            optional + 96
        )

    elif magic == PE32_PLUS_MAGIC:
        data_directory = (
            optional + 112
        )

    else:
        raise ValueError(
            "Unsupported PE optional header"
        )

    size_of_headers = _u32(
        data,
        optional + 60,
    )

    export_rva = 0

    if (
        data_directory + 8
        <= optional + optional_size
    ):
        export_rva = _u32(
            data,
            data_directory,
        )

    section_table = (
        optional + optional_size
    )

    sections = []

    for index in range(
        number_of_sections
    ):
        offset = (
            section_table
            + (index * 40)
        )

        if offset + 40 > len(data):
            raise ValueError(
                "Invalid section table"
            )

        sections.append({
            "virtual_size":
                _u32(
                    data,
                    offset + 8,
                ),

            "virtual_address":
                _u32(
                    data,
                    offset + 12,
                ),

            "raw_size":
                _u32(
                    data,
                    offset + 16,
                ),

            "raw_offset":
                _u32(
                    data,
                    offset + 20,
                ),
        })

    if machine == IMAGE_FILE_MACHINE_AMD64:
        architecture = "x64"

    elif machine == IMAGE_FILE_MACHINE_I386:
        architecture = "x86"

    else:
        architecture = "unknown"

    exports = _exports(
        data,
        export_rva,
        sections,
        size_of_headers,
    )

    return {
        "machine":
            machine,

        "architecture":
            architecture,

        "characteristics":
            characteristics,

        "is_dll":
            bool(
                characteristics
                & IMAGE_FILE_DLL
            ),

        "exports":
            exports,
    }
