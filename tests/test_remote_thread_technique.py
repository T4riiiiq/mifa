import unittest
from pathlib import Path

from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry


ROOT = Path(__file__).resolve().parents[1]


class RemoteThreadTechniqueTests(
    unittest.TestCase
):
    def setUp(self):
        self.registry = TechniqueRegistry(
            ROOT / "techniques"
        )

        self.method = self.registry.get(
            "remote-thread"
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
            self.method[
                "requires_payload"
            ]
        )

        self.assertEqual(
            self.method[
                "payload_types"
            ],
            ["raw"],
        )

    def test_x64_x86(self):
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

    def test_pid_runtime_argument(self):
        args = self.method[
            "runtime_arguments"
        ]

        self.assertEqual(
            args[0]["name"],
            "pid",
        )


class RemoteThreadTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (
            ROOT
            / "techniques"
            / "remote-thread"
            / "main.c.tpl"
        ).read_text()

    def test_target_architecture_check_present(self):
        self.assertTrue(
            "IsWow64Process2" in self.template
            or "IsWow64Process" in self.template
        )

    def test_checks_thread_completion(self):
        self.assertIn(
            "WaitForSingleObject",
            self.template,
        )

        self.assertIn(
            "GetExitCodeThread",
            self.template,
        )


if __name__ == "__main__":
    unittest.main()


class RemoteThreadRuntimeSemanticsTests(
    unittest.TestCase
):
    def setUp(self):
        self.template = (
            ROOT
            / "techniques"
            / "remote-thread"
            / "main.c.tpl"
        ).read_text()

    def test_timeout_means_thread_still_running(self):
        start = self.template.index(
            "else if (wait_status == WAIT_TIMEOUT)"
        )

        end = self.template.index(
            "else if (wait_status == WAIT_FAILED)",
            start,
        )

        timeout_block = self.template[
            start:end
        ]

        self.assertIn(
            "still running",
            timeout_block,
        )

        self.assertNotIn(
            "result = 1",
            timeout_block,
        )

        self.assertNotIn(
            "VirtualFreeEx",
            timeout_block,
        )
