import unittest
from pathlib import Path

from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry


ROOT = Path(__file__).resolve().parents[1]


class ProcessHollowingTechniqueTests(unittest.TestCase):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        self.method = self.registry.get(
            "process-hollowing"
        )

    def test_exists(self):
        self.assertIsNotNone(
            self.method
        )

    def test_contract_valid(self):
        self.assertEqual(
            MethodSchemaValidator().validate(
                self.method
            ),
            [],
        )

    def test_is_c(self):
        self.assertEqual(
            self.method["language"],
            "c",
        )

    def test_requires_raw_payload(self):
        self.assertTrue(
            self.method["requires_payload"]
        )

        self.assertEqual(
            self.method["payload_types"],
            ["raw"],
        )

    def test_x64_x86(self):
        self.assertEqual(
            set(self.method["architectures"]),
            {"x64", "x86"},
        )

    def test_file_and_external_providers(self):
        self.assertEqual(
            set(self.method["providers"]),
            {"file", "external", "msfvenom"},
        )

    def test_validation_is_runtime_tested(self):
        self.assertEqual(
            self.method["operational"]["validation"],
            "runtime-tested",
        )

    def test_optional_target_runtime_argument(self):
        args = self.method[
            "runtime_arguments"
        ]

        self.assertEqual(
            len(args),
            1,
        )

        self.assertEqual(
            args[0]["name"],
            "target",
        )

        self.assertEqual(
            args[0]["type"],
            "path",
        )

        self.assertFalse(
            args[0]["required"]
        )

    def test_source_contract(self):
        sources = self.method["sources"]

        self.assertGreaterEqual(
            len(sources),
            1,
        )

        main_sources = [
            src for src in sources
            if src.get("template") == "main.c.tpl"
        ]

        self.assertEqual(
            len(main_sources),
            1,
        )

        self.assertEqual(
            main_sources[0]["output"],
            "main.c",
        )

        self.assertTrue(
            main_sources[0]["compile"]
        )


class ProcessHollowingTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (
            ROOT
            / "techniques"
            / "process-hollowing"
            / "main.c.tpl"
        ).read_text()

    def test_payload_placeholders_present(self):
        self.assertIn(
            "{{PAYLOAD_BYTES_C}}",
            self.template,
        )

        self.assertIn(
            "{{PAYLOAD_BYTES_LEN}}",
            self.template,
        )

    def test_wrapper_calls_execution_core(self):
        self.assertIn(
            '#include "execution_core.h"',
            self.template,
        )

        self.assertIn(
            "execute_technique(",
            self.template,
        )

        self.assertIn(
            "if (result != 0)",
            self.template,
        )

        self.assertIn(
            "return 1;",
            self.template,
        )


class ProcessHollowingSemanticsTests(
    unittest.TestCase
):
    def setUp(self):
        self.core = (
            ROOT
            / "techniques"
            / "process-hollowing"
            / "execution_core.c.tpl"
        ).read_text()

    def test_entry_point_overwrite_flow_is_explicit(self):
        self.assertIn(
            "CREATE_SUSPENDED",
            self.core,
        )

        self.assertIn(
            "AddressOfEntryPoint",
            self.core,
        )

        self.assertIn(
            "WriteProcessMemory",
            self.core,
        )

        self.assertIn(
            "ResumeThread",
            self.core,
        )

    def test_display_name_describes_variant(self):
        self.assertEqual(
            TechniqueRegistry(
                ROOT / "techniques"
            ).get(
                "process-hollowing"
            )["name"],
            "Process Hollowing (Entry Point Overwrite)",
        )


class ProcessHollowingCorrectnessTests(
    unittest.TestCase
):
    def setUp(self):
        self.core = (
            ROOT
            / "techniques"
            / "process-hollowing"
            / "execution_core.c.tpl"
        ).read_text()

    def test_target_architecture_is_validated(self):
        self.assertIn(
            "IMAGE_FILE_MACHINE_AMD64",
            self.core,
        )

        self.assertIn(
            "IMAGE_FILE_MACHINE_I386",
            self.core,
        )

        self.assertIn(
            "Architecture mismatch",
            self.core,
        )

    def test_payload_is_bounded_by_target_image(self):
        self.assertIn(
            "SizeOfImage",
            self.core,
        )

        self.assertIn(
            "payload_len > (imageSize - entryPointRVA)",
            self.core,
        )

    def test_instruction_cache_is_flushed(self):
        write_index = self.core.index(
            "WriteProcessMemory"
        )

        flush_index = self.core.index(
            "FlushInstructionCache"
        )

        resume_index = self.core.index(
            "ResumeThread"
        )

        self.assertLess(
            write_index,
            flush_index,
        )

        self.assertLess(
            flush_index,
            resume_index,
        )

if __name__ == "__main__":
    unittest.main()
