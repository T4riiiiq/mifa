import unittest
from pathlib import Path

from core.reflective import ReflectiveContract
from core.techniques import TechniqueRegistry
from providers import get_provider


ROOT = Path(__file__).resolve().parents[1]


class ReflectiveBuiltinTests(
    unittest.TestCase
):
    def setUp(self):
        self.contract = (
            ReflectiveContract(ROOT)
        )

    def test_contract_valid(self):
        self.assertTrue(
            self.contract.validate(
                self.contract.load()
            )
        )

    def test_abi_version(self):
        self.assertEqual(
            self.contract.load()[
                "abi_version"
            ],
            1,
        )

    def test_required_export(self):
        self.assertEqual(
            self.contract.load()[
                "required_exports"
            ],
            ["ReflectiveLoader"],
        )

    def test_builtin_is_not_falsely_ready(self):
        self.assertFalse(
            self.contract.builtin_ready()
        )

    def test_provider_registered(self):
        provider = get_provider(
            "reflective-builtin"
        )

        self.assertEqual(
            provider.provider_id,
            "reflective-builtin",
        )

    def test_reflective_method_supports_builtin(self):
        method = TechniqueRegistry(
            ROOT / "techniques"
        ).get(
            "reflective-dll"
        )

        self.assertIn(
            "reflective-builtin",
            method["providers"],
        )

    def test_build_tested_builtin_can_be_used(self):
        provider = get_provider(
            "reflective-builtin"
        )

        result = provider.resolve(
            "builtin"
        )

        self.assertEqual(
            result["provider"],
            "reflective-builtin",
        )

        self.assertTrue(
            result["path"].is_file()
        )

        self.assertEqual(
            result["provenance"]["loader_abi"],
            1,
        )

        self.assertEqual(
            result["provenance"]["validation"],
            "build-tested",
        )


if __name__ == "__main__":
    unittest.main()


class ReflectiveBuiltinCompatibilityTests(
    unittest.TestCase
):
    def test_provider_supported_by_compatibility_engine(self):
        from core.compatibility import CompatibilityChecker

        self.assertIn(
            "reflective-builtin",
            CompatibilityChecker.SUPPORTED_PAYLOAD_PROVIDERS,
        )
