import unittest
from pathlib import Path

from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry
from core.operational_builder import OperationalBuilder


ROOT = Path(
    __file__
).resolve().parents[1]


class OperationalPipelineTests(
    unittest.TestCase
):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

    def test_package_technique_exists(self):
        method = self.registry.get(
            "package"
        )

        self.assertIsNotNone(
            method
        )

    def test_package_is_deployable(self):
        method = self.registry.get(
            "package"
        )

        self.assertTrue(
            method[
                "operational"
            ][
                "deployable"
            ]
        )

    def test_package_contract_valid(self):
        method = self.registry.get(
            "package"
        )

        errors = (
            MethodSchemaValidator()
            .validate(
                method
            )
        )

        self.assertEqual(
            errors,
            [],
        )

    def test_package_supports_x64_x86(self):
        method = self.registry.get(
            "package"
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

    def test_unknown_technique_rejected(self):
        builder = OperationalBuilder(
            ROOT
        )

        with self.assertRaisesRegex(
            ValueError,
            "Unknown operational technique",
        ):
            builder.build(
                technique="missing",
                architecture="x64",
                payload_source="/tmp/missing.bin",
            )

    def test_missing_payload_rejected(self):
        builder = OperationalBuilder(
            ROOT
        )

        with self.assertRaisesRegex(
            ValueError,
            "requires a payload",
        ):
            builder.build(
                technique="package",
                architecture="x64",
            )

    def test_invalid_architecture_rejected(self):
        builder = OperationalBuilder(
            ROOT
        )

        with self.assertRaisesRegex(
            ValueError,
            "Architecture",
        ):
            builder.build(
                technique="package",
                architecture="arm64",
                payload_source=__file__,
                payload_type="raw",
            )


if __name__ == "__main__":
    unittest.main()
