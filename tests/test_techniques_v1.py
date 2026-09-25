import unittest
from pathlib import Path

from core.compatibility import CompatibilityChecker
from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry


ROOT = Path(
    __file__
).resolve().parents[1]


class TechniquesV1Tests(
    unittest.TestCase
):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        self.schema = (
            MethodSchemaValidator()
        )

        self.compatibility = (
            CompatibilityChecker()
        )

        self.aliases = [
            "command",
            "local-dll",
            "script",
            "managed",
        ]

    def test_visible_aliases(self):
        aliases = {
            method[
                "operational"
            ][
                "alias"
            ]
            for method
            in self.registry.discover()
        }

        for alias in self.aliases:
            self.assertIn(
                alias,
                aliases,
            )

    def test_contracts_valid(self):
        for alias in self.aliases:
            method = self.registry.get(
                alias
            )

            self.assertEqual(
                self.schema.validate(
                    method
                ),
                [],
                alias,
            )

    def test_no_payload_required(self):
        for alias in self.aliases:
            method = self.registry.get(
                alias
            )

            self.assertFalse(
                method[
                    "requires_payload"
                ]
            )

            self.assertEqual(
                method[
                    "providers"
                ],
                [],
            )

    def test_architectures(self):
        for alias in self.aliases:
            method = self.registry.get(
                alias
            )

            self.assertEqual(
                set(
                    method[
                        "architectures"
                    ]
                ),
                {
                    "x64",
                    "x86",
                },
            )

    def test_command_arguments(self):
        method = self.registry.get(
            "command"
        )

        names = [
            item["name"]
            for item
            in method[
                "runtime_arguments"
            ]
        ]

        self.assertEqual(
            names,
            [
                "command"
            ],
        )

    def test_dll_arguments(self):
        method = self.registry.get(
            "local-dll"
        )

        names = [
            item["name"]
            for item
            in method[
                "runtime_arguments"
            ]
        ]

        self.assertEqual(
            names,
            [
                "dll_path"
            ],
        )

    def test_script_arguments(self):
        method = self.registry.get(
            "script"
        )

        names = [
            item["name"]
            for item
            in method[
                "runtime_arguments"
            ]
        ]

        self.assertEqual(
            names,
            [
                "script_path",
                "arguments",
            ],
        )

    def test_managed_arguments(self):
        method = self.registry.get(
            "managed"
        )

        names = [
            item["name"]
            for item
            in method[
                "runtime_arguments"
            ]
        ]

        self.assertEqual(
            names,
            [
                "application",
                "arguments",
            ],
        )


if __name__ == "__main__":
    unittest.main()
