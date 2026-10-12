BANNER = r"""
███╗   ███╗ ██╗ ███████╗  █████╗
████╗ ████║ ██║ ██╔════╝ ██╔══██╗
██╔████╔██║ ██║ █████╗   ███████║
██║╚██╔╝██║ ██║ ██╔══╝   ██╔══██║
██║ ╚═╝ ██║ ██║ ██║      ██║  ██║
╚═╝     ╚═╝ ╚═╝ ╚═╝      ╚═╝  ╚═╝
"""


TAGLINE = "Technique → Payload → Build"


def render_banner(
    theme
):
    logo = theme.style(
        BANNER.strip("\n"),
        theme.BOLD,
        theme.CYAN,
    )

    tagline = theme.dim(
        TAGLINE
    )

    return (
        "\n"
        + logo
        + "\n\n"
        + "        "
        + tagline
        + "\n"
    )
