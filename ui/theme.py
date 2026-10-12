import os
import sys


class Theme:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"

    def __init__(
        self,
        enabled=True
    ):
        self.enabled = bool(
            enabled
            and sys.stdout.isatty()
            and os.environ.get(
                "NO_COLOR"
            ) is None
        )

    def style(
        self,
        text,
        *codes
    ):
        text = str(text)

        if not self.enabled:
            return text

        return (
            "".join(codes)
            + text
            + self.RESET
        )

    def bold(self, text):
        return self.style(
            text,
            self.BOLD
        )

    def dim(self, text):
        return self.style(
            text,
            self.DIM
        )

    def cyan(self, text):
        return self.style(
            text,
            self.CYAN
        )

    def green(self, text):
        return self.style(
            text,
            self.GREEN
        )

    def yellow(self, text):
        return self.style(
            text,
            self.YELLOW
        )

    def red(self, text):
        return self.style(
            text,
            self.RED
        )

    def magenta(self, text):
        return self.style(
            text,
            self.MAGENTA
        )
