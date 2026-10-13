import unittest

from core.readiness import (
    is_buildable,
    readiness_for,
)


def method_with(
    validation
):
    return {
        "operational": {
            "validation": validation,
        }
    }


class ReadinessTests(
    unittest.TestCase
):
    def test_runtime_tested_is_ready(self):
        result = readiness_for(
            method_with(
                "runtime-tested"
            )
        )

        self.assertEqual(
            result["label"],
            "✓ READY"
        )

        self.assertTrue(
            result["buildable"]
        )

    def test_build_tested_is_buildable(self):
        result = readiness_for(
            method_with(
                "build-tested"
            )
        )

        self.assertEqual(
            result["label"],
            "BUILD OK"
        )

        self.assertTrue(
            result["buildable"]
        )

    def test_planned_is_not_buildable(self):
        result = readiness_for(
            method_with(
                "planned"
            )
        )

        self.assertEqual(
            result["label"],
            "PLANNED"
        )

        self.assertFalse(
            result["buildable"]
        )

    def test_unknown_fails_closed(self):
        result = readiness_for(
            method_with(
                "unexpected-state"
            )
        )

        self.assertEqual(
            result["label"],
            "UNKNOWN"
        )

        self.assertFalse(
            result["buildable"]
        )

    def test_is_buildable_uses_readiness(self):
        self.assertTrue(
            is_buildable(
                method_with(
                    "runtime-tested"
                )
            )
        )

        self.assertFalse(
            is_buildable(
                method_with(
                    "planned"
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
