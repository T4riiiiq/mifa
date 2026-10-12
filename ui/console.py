from ui.theme import Theme


class Console:
    def __init__(
        self,
        color=True,
        verbose=False
    ):
        self.theme = Theme(
            enabled=color
        )

        self.verbose = verbose

    def print(
        self,
        text=""
    ):
        print(text)

    def success(
        self,
        text
    ):
        print(
            f"{self.theme.green('✓')} "
            f"{text}"
        )

    def info(
        self,
        text
    ):
        print(
            f"{self.theme.cyan('›')} "
            f"{text}"
        )

    def warning(
        self,
        text
    ):
        print(
            f"{self.theme.yellow('!')} "
            f"{text}"
        )

    def error(
        self,
        text
    ):
        print(
            f"{self.theme.red('✗')} "
            f"{text}"
        )

    def heading(
        self,
        text
    ):
        print(
            self.theme.style(
                text,
                self.theme.BOLD,
                self.theme.CYAN,
            )
        )

    def label(
        self,
        name,
        value
    ):
        label = f"{str(name):<14}"

        print(
            "  "
            + self.theme.dim(label)
            + " : "
            + str(value)
        )

    def detail(
        self,
        text
    ):
        if self.verbose:
            print(
                self.theme.dim(
                    text
                )
            )
