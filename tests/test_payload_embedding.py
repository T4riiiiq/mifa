import tempfile
import unittest
from pathlib import Path

from core.generator import SourceGenerator


class PayloadEmbeddingTests(
    unittest.TestCase
):
    def test_staged_payload_is_embedded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            method_dir = (
                root / "method"
            )

            build_dir = (
                root / "build"
            )

            input_dir = (
                build_dir / "input"
            )

            method_dir.mkdir()
            input_dir.mkdir(
                parents=True
            )

            (
                method_dir
                / "main.cpp.tpl"
            ).write_text(
                """
unsigned char payload[] = {
{{PAYLOAD_BYTES_C}}
};

unsigned long payload_len =
{{PAYLOAD_BYTES_LEN}};
""",
                encoding="utf-8",
            )

            staged = (
                input_dir
                / "payload.bin"
            )

            staged.write_bytes(
                bytes.fromhex("90 90 c3")
            )

            method = {
                "_path":
                    str(method_dir),

                "parameters":
                    {},

                "sources": [
                    {
                        "template":
                            "main.cpp.tpl",

                        "output":
                            "main.cpp",

                        "compile":
                            True,
                    }
                ],
            }

            payload_info = {
                "staged": {
                    "file":
                        "input/payload.bin",
                },

                "pipeline":
                    None,
            }

            generated = (
                SourceGenerator()
                .generate(
                    method=method,
                    preset={
                        "architecture":
                            "x64",

                        "build_type":
                            "release",
                    },
                    build_id="K-0001",
                    build_dir=build_dir,
                    payload_info=payload_info,
                    payload_type="raw",
                    parameters={},
                )
            )

            text = (
                generated[0]["path"]
                .read_text(
                    encoding="utf-8"
                )
            )

            self.assertIn(
                "0x90, 0x90, 0xc3",
                text,
            )

            self.assertIn(
                "3;",
                text,
            )


if __name__ == "__main__":
    unittest.main()
