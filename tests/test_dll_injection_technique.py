import unittest
from pathlib import Path

from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry


ROOT = Path(__file__).resolve().parents[1]


class DLLInjectionTechniqueTests(
    unittest.TestCase
):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        self.method = self.registry.get(
            "dll-injection"
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

    def test_language_is_c(self):
        self.assertEqual(
            self.method["language"],
            "c",
        )

    def test_requires_dll(self):
        contract = self.method[
            "payload_contract"
        ]

        self.assertEqual(
            contract["types"],
            ["pe"],
        )

        self.assertEqual(
            contract["pe_kind"],
            "dll",
        )

    def test_architectures(self):
        self.assertEqual(
            set(
                self.method[
                    "architectures"
                ]
            ),
            {
                "x64",
                "x86",
            },
        )

    def test_pid_argument(self):
        self.assertEqual(
            self.method[
                "runtime_arguments"
            ][0]["name"],
            "pid",
        )


class DLLInjectionExecutionTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (
            ROOT
            / "techniques"
            / "dll-injection"
            / "main.c.tpl"
        ).read_text(encoding="utf-8")

    def test_stages_embedded_dll_to_disk(self):
        self.assertIn("CreateFileA", self.template)
        self.assertIn("WriteFile", self.template)
        self.assertIn("mifa_%lu_%lu.dll", self.template)

    def test_remote_buffer_contains_path_not_dll_bytes(self):
        self.assertIn("WriteProcessMemory", self.template)
        self.assertIn("remote_path", self.template)
        self.assertIn("dll_path", self.template)
        self.assertIn("LoadLibraryA", self.template)

    def test_keeps_core_interface(self):
        self.assertIn("execute_technique", self.template)
        self.assertIn("const unsigned char *payload", self.template)
        self.assertIn("SIZE_T payload_len", self.template)
        self.assertIn("DWORD pid", self.template)

    def test_checks_thread_result(self):
        self.assertIn("GetExitCodeThread", self.template)
        self.assertIn("thread_exit_code == 0", self.template)


class DLLInjectionTemplateTests(
    unittest.TestCase
):
    def test_target_architecture_check_present(self):
        template = (
            ROOT
            / "techniques"
            / "dll-injection"
            / "main.c.tpl"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "IsWow64Process2",
            template,
        )

        self.assertIn(
            "Architecture mismatch",
            template,
        )

        self.assertIn(
            "PROCESS_QUERY_INFORMATION",
            template,
        )

class DLLInjectionDiagnosticTests(
    unittest.TestCase
):
    def setUp(self):
        self.template = (
            ROOT
            / "techniques"
            / "dll-injection"
            / "main.c.tpl"
        ).read_text(
            encoding="utf-8"
        )

    def test_has_operation_specific_win32_diagnostics(self):
        self.assertIn(
            "report_win32_error",
            self.template,
        )

        for operation in (
            "OpenProcess",
            "VirtualAllocEx",
            "WriteProcessMemory",
            "CreateRemoteThread",
            "WaitForSingleObject",
            "GetExitCodeThread",
        ):
            self.assertIn(
                f'"{operation}"',
                self.template,
            )

    def test_main_does_not_report_stale_last_error(self):
        self.assertNotIn(
            "DLL Injection failed: %d (Win32=%lu)",
            self.template,
        )

        self.assertIn(
            "DLL Injection failed: %d",
            self.template,
        )

    def test_internal_failures_have_explicit_messages(self):
        self.assertIn(
            "Remote path write truncated",
            self.template,
        )

        self.assertIn(
            "LoadLibraryA returned NULL in the target process",
            self.template,
        )

        self.assertIn(
            "Unexpected wait status",
            self.template,
        )


if __name__ == "__main__":
    unittest.main()
