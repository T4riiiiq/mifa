from pathlib import Path
import hashlib
import json
import re
import struct


class BuildPreflight:
    BUILD_ID = re.compile(
        r"^K-\d{4}$"
    )

    MACHINES = {
        0x014C:
            "x86",

        0x8664:
            "x64",

        0xAA64:
            "arm64",
    }

    def __init__(
        self,
        root: Path
    ):
        self.root = Path(
            root
        )

    def _sha256(
        self,
        path
    ):
        digest = hashlib.sha256()

        with Path(path).open(
            "rb"
        ) as handle:
            while True:
                chunk = handle.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(
                    chunk
                )

        return digest.hexdigest()

    def _pe_architecture(
        self,
        path
    ):
        data = Path(
            path
        ).read_bytes()

        if (
            len(data) < 0x40
            or data[:2] != b"MZ"
        ):
            return None

        pe_offset = struct.unpack_from(
            "<I",
            data,
            0x3C,
        )[0]

        if (
            pe_offset + 6
            > len(data)
        ):
            return None

        if (
            data[
                pe_offset:
                pe_offset + 4
            ]
            != b"PE\x00\x00"
        ):
            return None

        machine = struct.unpack_from(
            "<H",
            data,
            pe_offset + 4,
        )[0]

        return self.MACHINES.get(
            machine,
            f"0x{machine:04x}",
        )

    def verify(
        self,
        build_id
    ):
        if not self.BUILD_ID.match(
            build_id
        ):
            raise ValueError(
                f"Invalid build ID: {build_id}"
            )

        build_dir = (
            self.root
            / "builds"
            / build_id
        )

        manifest_path = (
            build_dir
            / "build.json"
        )

        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Build not found: {build_id}"
            )

        data = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

        output = (
            data.get(
                "output"
            )
            or {}
        )

        output_file = output.get(
            "file"
        )

        artifact = (
            build_dir
            / output_file
            if output_file
            else None
        )

        exists = bool(
            artifact
            and artifact.exists()
            and artifact.is_file()
        )

        expected_hash = output.get(
            "sha256"
        )

        actual_hash = (
            self._sha256(
                artifact
            )
            if exists
            else None
        )

        hash_match = (
            actual_hash.lower()
            == expected_hash.lower()
            if (
                actual_hash
                and expected_hash
            )
            else None
        )

        expected_arch = (
            data.get(
                "preset",
                {}
            ).get(
                "architecture"
            )
        )

        actual_arch = (
            self._pe_architecture(
                artifact
            )
            if exists
            else None
        )

        arch_match = None

        if (
            actual_arch
            in {
                "x86",
                "x64",
                "arm64",
            }
            and expected_arch
        ):
            arch_match = (
                actual_arch
                == expected_arch
            )

        payload = (
            data.get(
                "payload"
            )
            or {}
        )

        pipeline = (
            payload.get(
                "pipeline"
            )
            or {}
        )

        roundtrip = (
            pipeline.get(
                "roundtrip_match"
            )
            if pipeline
            else None
        )

        overall = (
            data.get(
                "status"
            )
            == "success"
            and exists
            and hash_match is not False
            and arch_match is not False
            and roundtrip is not False
        )

        return {
            "build_id":
                build_id,

            "status":
                data.get(
                    "status"
                ),

            "artifact":
                str(
                    artifact
                )
                if artifact
                else None,

            "artifact_exists":
                exists,

            "expected_sha256":
                expected_hash,

            "actual_sha256":
                actual_hash,

            "hash_match":
                hash_match,

            "expected_arch":
                expected_arch,

            "actual_arch":
                actual_arch,

            "arch_match":
                arch_match,

            "payload_roundtrip":
                roundtrip,

            "result":
                (
                    "PASS"
                    if overall
                    else "FAIL"
                ),
        }
