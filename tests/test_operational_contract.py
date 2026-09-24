import copy
import unittest

from core.compatibility import CompatibilityChecker
from core.schema import MethodSchemaValidator


def valid_method():
    return {
        "id": "demo-operational",
        "name": "Demo Operational Method",
        "language": "cpp",
        "architectures": [
            "x64",
            "x86",
        ],
        "build_types": [
            "release",
            "debug",
        ],
        "operational": {
            "alias": "demo",
            "category": "Execution",
            "runtime": "native",
            "privilege": "user",
            "deployable": True,
            "validation": "planned",
        },
        "requires_payload": True,
        "payload_types": [
            "raw",
        ],
        "payload_contract": {
            "required": True,
            "types": [
                "raw",
            ],
            "transforms": [
                "copy",
            ],
            "default_transform": "copy",
            "min_size_bytes": 1,
            "max_size_bytes": 10485760,
        },
        "providers": [
            "file",
            "external",
        ],
        "parameters": {},
        "runtime_arguments": [],
        "sources": [
            {
                "template": "main.cpp.tpl",
                "output": "main.cpp",
                "compile": True,
            },
        ],
        "output_name": "demo.exe",
    }


class OperationalContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = MethodSchemaValidator()
        self.compatibility = CompatibilityChecker()

    def test_valid_operational_contract(self):
        self.assertEqual(
            self.schema.validate(
                valid_method()
            ),
            [],
        )

    def test_operational_metadata_required(self):
        method = valid_method()
        del method["operational"]

        errors = self.schema.validate(
            method
        )

        self.assertTrue(
            any(
                "operational"
                in error
                for error in errors
            )
        )

    def test_legacy_technique_metadata_rejected(self):
        method = valid_method()
        method["technique"] = {
            "alias": "old",
        }

        errors = self.schema.validate(
            method
        )

        self.assertTrue(
            any(
                "legacy technique"
                in error
                for error in errors
            )
        )

    def test_payload_method_requires_provider(self):
        method = valid_method()
        method["providers"] = []

        errors = self.schema.validate(
            method
        )

        self.assertTrue(
            any(
                "at least one provider"
                in error
                for error in errors
            )
        )

    def test_provider_compatibility(self):
        method = valid_method()

        errors = self.compatibility.validate(
            method=method,
            preset={
                "architecture": "x64",
                "build_type": "release",
            },
            payload_path="/tmp/payload.bin",
            payload_type="raw",
            payload_transform="copy",
            payload_provider="file",
        )

        self.assertEqual(
            errors,
            [],
        )

    def test_unsupported_method_provider_rejected(self):
        method = valid_method()

        errors = self.compatibility.validate(
            method=method,
            preset={
                "architecture": "x64",
                "build_type": "release",
            },
            payload_path="/tmp/payload.bin",
            payload_type="raw",
            payload_transform="copy",
            payload_provider="fixture",
        )

        self.assertTrue(
            any(
                "not supported by method"
                in error
                for error in errors
            )
        )

    def test_payload_requires_provider_selection(self):
        method = valid_method()

        errors = self.compatibility.validate(
            method=method,
            preset={
                "architecture": "x64",
                "build_type": "release",
            },
            payload_path="/tmp/payload.bin",
            payload_type="raw",
            payload_transform="copy",
        )

        self.assertIn(
            "Payload provider must be specified",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
