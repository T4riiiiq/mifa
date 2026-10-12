import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from providers.msfvenom import MsfvenomProvider


class MsfvenomAdapterTests(unittest.TestCase):

    def _fake_msfvenom(
        self,
        directory: Path,
        args_log: Path
    ):
        fake = directory / "msfvenom"

        fake.write_text(
            f"""#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]

pathlib.Path(
    {str(args_log)!r}
).write_text(
    json.dumps(args)
)

if "-o" not in args:
    sys.exit(2)

output = pathlib.Path(
    args[args.index("-o") + 1]
)

# Benign synthetic bytes for provider tests.
output.write_bytes(
    bytes.fromhex("90C3")
)

sys.exit(0)
"""
        )

        fake.chmod(0o755)

        return fake

    def _fake_compiler(
        self,
        directory: Path,
        name: str,
        fail=False
    ):
        compiler = directory / name

        if fail:
            body = """#!/usr/bin/env python3
import sys
sys.exit(9)
"""
        else:
            body = """#!/usr/bin/env python3
import pathlib
import sys

args = sys.argv[1:]

if "-o" not in args:
    sys.exit(2)

output = pathlib.Path(
    args[args.index("-o") + 1]
)

output.write_bytes(
    b"MIFA-DLL-ADAPTER-TEST"
)

sys.exit(0)
"""

        compiler.write_text(
            body
        )

        compiler.chmod(0o755)

        return compiler

    def test_dll_x64_uses_adapter(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()

            args_log = root / "msf-args.json"

            self._fake_msfvenom(
                bin_dir,
                args_log
            )

            self._fake_compiler(
                bin_dir,
                "x86_64-w64-mingw32-gcc"
            )

            env = os.environ.copy()

            env["PATH"] = (
                str(bin_dir)
                + os.pathsep
                + env.get("PATH", "")
            )

            with patch.dict(
                os.environ,
                env,
                clear=True
            ):
                result = (
                    MsfvenomProvider()
                    .resolve(
                        "windows/x64/test",
                        format="dll",
                        architecture="x64",
                        output_dir=root,
                    )
                )

            provenance = result[
                "provenance"
            ]

            self.assertTrue(
                result["path"].exists()
            )

            self.assertEqual(
                provenance["format"],
                "dll",
            )

            self.assertEqual(
                provenance["strategy"],
                "adapter",
            )

            self.assertEqual(
                provenance["generator_format"],
                "raw",
            )

            self.assertEqual(
                provenance["compiler"],
                "x86_64-w64-mingw32-gcc",
            )

    def test_dll_x86_uses_adapter(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()

            args_log = root / "msf-args.json"

            self._fake_msfvenom(
                bin_dir,
                args_log
            )

            self._fake_compiler(
                bin_dir,
                "i686-w64-mingw32-gcc"
            )

            env = os.environ.copy()

            env["PATH"] = (
                str(bin_dir)
                + os.pathsep
                + env.get("PATH", "")
            )

            with patch.dict(
                os.environ,
                env,
                clear=True
            ):
                result = (
                    MsfvenomProvider()
                    .resolve(
                        "windows/test",
                        format="dll",
                        architecture="x86",
                        output_dir=root,
                    )
                )

            provenance = result[
                "provenance"
            ]

            self.assertEqual(
                provenance["architecture"],
                "x86",
            )

            self.assertEqual(
                provenance["strategy"],
                "adapter",
            )

            self.assertEqual(
                provenance["compiler"],
                "i686-w64-mingw32-gcc",
            )

    def test_dll_adapter_requests_raw_from_msfvenom(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()

            args_log = root / "msf-args.json"

            self._fake_msfvenom(
                bin_dir,
                args_log
            )

            self._fake_compiler(
                bin_dir,
                "x86_64-w64-mingw32-gcc"
            )

            env = os.environ.copy()

            env["PATH"] = (
                str(bin_dir)
                + os.pathsep
                + env.get("PATH", "")
            )

            with patch.dict(
                os.environ,
                env,
                clear=True
            ):
                MsfvenomProvider().resolve(
                    "windows/x64/test",
                    format="dll",
                    architecture="x64",
                    output_dir=root,
                )

            args = json.loads(
                args_log.read_text()
            )

            format_index = (
                args.index("-f")
            )

            self.assertEqual(
                args[format_index + 1],
                "raw",
            )

    def test_raw_remains_direct(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()

            args_log = root / "msf-args.json"

            self._fake_msfvenom(
                bin_dir,
                args_log
            )

            env = os.environ.copy()

            env["PATH"] = (
                str(bin_dir)
                + os.pathsep
                + env.get("PATH", "")
            )

            with patch.dict(
                os.environ,
                env,
                clear=True
            ):
                result = (
                    MsfvenomProvider()
                    .resolve(
                        "windows/x64/test",
                        format="raw",
                        architecture="x64",
                        output_dir=root,
                    )
                )

            provenance = result[
                "provenance"
            ]

            self.assertEqual(
                provenance["strategy"],
                "direct",
            )

            self.assertEqual(
                provenance["generator_format"],
                "raw",
            )

            self.assertIsNone(
                provenance["compiler"]
            )

    def test_adapter_compile_failure_cleans_artifacts(
        self
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()

            args_log = root / "msf-args.json"

            self._fake_msfvenom(
                bin_dir,
                args_log
            )

            self._fake_compiler(
                bin_dir,
                "x86_64-w64-mingw32-gcc",
                fail=True
            )

            env = os.environ.copy()

            env["PATH"] = (
                str(bin_dir)
                + os.pathsep
                + env.get("PATH", "")
            )

            with patch.dict(
                os.environ,
                env,
                clear=True
            ):
                with self.assertRaises(
                    RuntimeError
                ):
                    MsfvenomProvider().resolve(
                        "windows/x64/test",
                        format="dll",
                        architecture="x64",
                        output_dir=root,
                    )

            self.assertEqual(
                list(
                    root.glob(
                        "msfvenom-*.dll"
                    )
                ),
                [],
            )

            self.assertEqual(
                list(
                    root.glob(
                        ".msfvenom-*.bin"
                    )
                ),
                [],
            )

            self.assertEqual(
                list(
                    root.glob(
                        ".*.adapter.c"
                    )
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()
