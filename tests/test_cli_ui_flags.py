import sys
import unittest
from unittest.mock import patch

import mifa


class CliUiFlagTests(unittest.TestCase):
    def test_ui_flags_only_open_interactive_mode(self):
        cases = [
            (
                ["mifa.py", "--verbose"],
                True,
                True,
            ),
            (
                ["mifa.py", "--no-color"],
                False,
                False,
            ),
            (
                [
                    "mifa.py",
                    "--verbose",
                    "--no-color",
                ],
                False,
                True,
            ),
        ]

        for argv, color, verbose in cases:
            with self.subTest(argv=argv):
                with (
                    patch.object(
                        sys,
                        "argv",
                        argv,
                    ),
                    patch(
                        "mifa.configure_console"
                    ) as configure,
                    patch(
                        "mifa.interactive_menu",
                        return_value=0,
                    ) as interactive,
                ):
                    result = mifa.main()

                self.assertEqual(
                    result,
                    0,
                )

                configure.assert_called_once_with(
                    color=color,
                    verbose=verbose,
                )

                interactive.assert_called_once_with()

    def test_help_does_not_enter_interactive_mode(self):
        with (
            patch.object(
                sys,
                "argv",
                [
                    "mifa.py",
                    "--help",
                ],
            ),
            patch(
                "mifa.interactive_menu"
            ) as interactive,
        ):
            with self.assertRaises(
                SystemExit
            ) as exc:
                mifa.main()

        self.assertEqual(
            exc.exception.code,
            0,
        )

        interactive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
