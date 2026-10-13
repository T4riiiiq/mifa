import unittest
from pathlib import Path

from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry


ROOT = Path(__file__).resolve().parents[1]


class ReflectiveDLLTechniqueTests(
    unittest.TestCase
):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        self.method = self.registry.get(
            "reflective-dll"
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

    def test_language_is_cpp(self):
        self.assertEqual(
            self.method["language"],
            "cpp",
        )

    def test_requires_dll(self):
        contract = self.method[
            "payload_contract"
        ]

        self.assertEqual(
            contract["pe_kind"],
            "dll",
        )

    def test_requires_reflective_loader_export(self):
        contract = self.method[
            "payload_contract"
        ]

        self.assertEqual(
            contract[
                "required_exports"
            ],
            ["ReflectiveLoader"],
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
            },
        )

    def test_pid_argument(self):
        self.assertEqual(
            self.method[
                "runtime_arguments"
            ][0]["name"],
            "pid",
        )


if __name__ == "__main__":
    unittest.main()


class ReflectiveDLLDiagnosticTests(
    unittest.TestCase
):
    def test_runtime_template_has_named_win32_errors(self):
        template = (
            ROOT
            / "techniques"
            / "reflective-dll"
            / "main.c.tpl"
        ).read_text()

        self.assertIn(
            "FormatMessageA",
            template
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
                template
            )

    def test_runtime_template_avoids_numeric_only_failure(self):
        template = (
            ROOT
            / "techniques"
            / "reflective-dll"
            / "main.c.tpl"
        ).read_text()

        self.assertNotIn(
            "Technique failed: %d",
            template
        )
