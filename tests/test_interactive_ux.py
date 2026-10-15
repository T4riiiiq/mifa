import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import mifa


def make_method(
    alias,
    name,
    providers,
    architectures=None,
):
    return {
        "name": name,
        "architectures": architectures or [
            "x64",
            "x86",
        ],
        "requires_payload": True,
        "providers": providers,
        "payload_contract": {
            "types": ["raw"],
            "transforms": ["copy"],
        },
        "operational": {
            "alias": alias,
            "category": "execution",
            "runtime": "windows",
            "validation": "runtime-tested",
        },
    }


class InteractiveUxTests(unittest.TestCase):
    def test_interactive_msfvenom_uses_x64_and_redacts_options(self):
        method = make_method(
            "dll-injection",
            "DLL Injection",
            ["file", "external", "msfvenom"],
        )

        builder = MagicMock()
        builder.registry.get.return_value = method
        builder.build.return_value = object()

        output = io.StringIO()

        with (
            patch(
                "builtins.input",
                side_effect=[
                    "windows/x64/exec",
                    "TOKEN=supersensitivevalue",
                    "",
                ],
            ),
            patch(
                "mifa.print_result"
            ),
            redirect_stdout(output),
        ):
            result = mifa.interactive_build(
                builder,
                technique="dll-injection",
            )

        self.assertTrue(result)

        kwargs = (
            builder.build.call_args.kwargs
        )

        self.assertEqual(
            kwargs["architecture"],
            "x64",
        )
        self.assertEqual(
            kwargs["provider_id"],
            "msfvenom",
        )
        self.assertEqual(
            kwargs["payload_source"],
            "windows/x64/exec",
        )
        self.assertEqual(
            kwargs["provider_options"][
                "msf_options"
            ],
            [
                "TOKEN=supersensitivevalue"
            ],
        )

        rendered = output.getvalue()

        self.assertIn(
            "TOKEN=<redacted>",
            rendered,
        )
        self.assertNotIn(
            "supersensitivevalue",
            rendered,
        )

    def test_invalid_payload_module_stays_in_prompt(self):
        method = make_method(
            "remote-thread",
            "Remote Thread Injection",
            ["file", "external", "msfvenom"],
        )

        builder = MagicMock()
        builder.registry.get.return_value = method
        builder.build.return_value = object()

        output = io.StringIO()

        with (
            patch(
                "builtins.input",
                side_effect=[
                    "x86",
                    "windows/x64/exec",
                    "",
                    "",
                ],
            ),
            patch(
                "mifa.print_result"
            ),
            redirect_stdout(output),
        ):
            result = mifa.interactive_build(
                builder,
                technique="remote-thread",
            )

        self.assertTrue(result)

        self.assertIn(
            "supports Windows x64 payload "
            "modules only",
            output.getvalue(),
        )

        self.assertEqual(
            builder.build.call_args.kwargs[
                "payload_source"
            ],
            "windows/x64/exec",
        )

    def test_reflective_uses_builtin_provider_automatically(self):
        method = make_method(
            "reflective-dll",
            "Reflective DLL Injection",
            [
                "reflective-builtin",
                "file",
                "external",
            ],
            architectures=["x64"],
        )

        builder = MagicMock()
        builder.registry.get.return_value = method
        builder.build.return_value = object()

        output = io.StringIO()

        with (
            patch(
                "builtins.input",
                side_effect=[""],
            ),
            patch(
                "mifa.print_result"
            ),
            redirect_stdout(output),
        ):
            result = mifa.interactive_build(
                builder,
                technique="reflective-dll",
            )

        self.assertTrue(result)

        kwargs = (
            builder.build.call_args.kwargs
        )

        self.assertEqual(
            kwargs["architecture"],
            "x64",
        )
        self.assertEqual(
            kwargs["provider_id"],
            "reflective-builtin",
        )
        self.assertEqual(
            kwargs["payload_source"],
            "builtin",
        )

        rendered = output.getvalue()

        self.assertIn(
            "Using Mifa built-in reflective DLL",
            rendered,
        )
        self.assertNotIn(
            "Payload module",
            rendered,
        )

    def test_techniques_command_hides_x86(self):
        method = make_method(
            "dll-injection",
            "DLL Injection",
            ["msfvenom"],
            architectures=[
                "x64",
                "x86",
            ],
        )

        registry = MagicMock()
        registry.discover.return_value = [
            method
        ]

        output = io.StringIO()

        with redirect_stdout(output):
            mifa.show_techniques(
                registry
            )

        rendered = output.getvalue()

        self.assertIn(
            "x64",
            rendered,
        )
        self.assertNotIn(
            "x86",
            rendered,
        )

    def test_main_menu_does_not_show_ready_status(self):
        method = make_method(
            "dll-injection",
            "DLL Injection",
            ["msfvenom"],
        )

        builder = MagicMock()
        builder.registry.discover.return_value = [
            method
        ]

        output = io.StringIO()

        with (
            patch(
                "mifa.OperationalBuilder",
                return_value=builder,
            ),
            patch(
                "builtins.input",
                side_effect=["q"],
            ),
            redirect_stdout(output),
        ):
            result = mifa.interactive_menu()

        self.assertEqual(
            result,
            0,
        )

        rendered = output.getvalue()

        self.assertIn(
            "DLL Injection",
            rendered,
        )
        self.assertNotIn(
            "READY",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
