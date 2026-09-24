import unittest
from pathlib import Path

from core.compatibility import CompatibilityChecker
from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry


ROOT = Path(
    __file__
).resolve().parents[1]


class NativeTechniqueTests(unittest.TestCase):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        self.method = self.registry.get(
            "native"
        )

    def test_native_is_visible(self):
        aliases = {
            method[
                "operational"
            ][
                "alias"
            ]
            for method
            in self.registry.discover()
        }

        self.assertIn(
            "native",
            aliases,
        )

    def test_native_contract_valid(self):
        self.assertIsNotNone(
            self.method
        )

        errors = (
            MethodSchemaValidator()
            .validate(
                self.method
            )
        )

        self.assertEqual(
            errors,
            [],
        )

    def test_native_has_no_payload(self):
        self.assertFalse(
            self.method[
                "requires_payload"
            ]
        )

        self.assertEqual(
            self.method[
                "providers"
            ],
            [],
        )

    def test_native_runtime_arguments(self):
        arguments = {
            item[
                "name"
            ]:
            item
            for item
            in self.method[
                "runtime_arguments"
            ]
        }

        self.assertIn(
            "application",
            arguments,
        )

        self.assertTrue(
            arguments[
                "application"
            ][
                "required"
            ]
        )

        self.assertIn(
            "arguments",
            arguments,
        )

    def test_native_is_runtime_tested(self):
        self.assertEqual(
            self.method[
                "operational"
            ][
                "validation"
            ],
            "runtime-tested",
        )

    def test_native_uses_unicode_entrypoint(self):
        self.assertIn(
            "-municode",
            self.method.get(
                "compiler_flags",
                []
            ),
        )

    def test_native_supports_x64_x86(self):
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

    def test_native_compatibility_without_payload(self):
        errors = (
            CompatibilityChecker()
            .validate(
                method=self.method,
                preset={
                    "architecture": "x64",
                    "build_type": "release",
                },
            )
        )

        self.assertEqual(
            errors,
            [],
        )


if __name__ == "__main__":
    unittest.main()
