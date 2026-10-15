#!/usr/bin/env python3

import argparse
import json
import shlex
import sys
from pathlib import Path

from core.operational_builder import OperationalBuilder
from core.preflight import BuildPreflight
from core.readiness import readiness_for
from core.reporting import ReportExporter
from providers import list_providers
from ui.banner import render_banner
from ui.console import Console


ROOT = Path(__file__).resolve().parent
CONSOLE = Console()


def configure_console(
    color=True,
    verbose=False
):
    global CONSOLE

    CONSOLE = Console(
        color=color,
        verbose=verbose,
    )


def banner():
    print(
        render_banner(
            CONSOLE.theme
        )
    )


def choose(
    title,
    options
):
    clean_title = str(title).strip().rstrip(":")

    print()
    CONSOLE.heading(
        clean_title
    )

    print()

    for index, option in enumerate(
        options,
        start=1
    ):
        number = CONSOLE.theme.cyan(
            str(index)
        )

        print(
            f"  {number}  {option}"
        )

    while True:
        value = input(
            "\n> "
        ).strip()

        try:
            index = int(value) - 1

        except ValueError:
            CONSOLE.error(
                "Invalid selection"
            )
            continue

        if 0 <= index < len(options):
            return options[index]

        CONSOLE.error(
            "Invalid selection"
        )


def load_manifest(
    build_id
):
    path = (
        ROOT
        / "builds"
        / build_id
        / "build.json"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Build not found: {build_id}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def show_techniques(
    registry,
    include_hidden=False
):
    techniques = registry.discover(
        include_hidden=include_hidden
    )

    if not techniques:
        print(
            "No user-facing operational "
            "techniques available."
        )

        return

    print()
    print(
        f"{'Alias':<22}"
        f"{'Category':<18}"
        f"{'Runtime':<12}"
        f"{'Validation':<18}"
        f"Architectures"
    )

    print("-" * 96)

    for method in techniques:
        operational = method[
            "operational"
        ]

        architectures = (
            "x64"
            if "x64" in method.get(
                "architectures",
                []
            )
            else "-"
        )

        validation = operational.get(
            "validation",
            "?"
        )

        print(
            f"{operational['alias']:<22}"
            f"{operational['category']:<18}"
            f"{operational['runtime']:<12}"
            f"{validation:<18}"
            f"{architectures}"
        )


def show_builds(
    include_all=False
):
    manifests = sorted(
        (
            ROOT
            / "builds"
        ).glob(
            "K-*/build.json"
        ),
        reverse=True,
    )

    if not manifests:
        CONSOLE.warning(
            "No builds found"
        )
        return

    total = len(manifests)

    if not include_all:
        manifests = manifests[:15]

    print()
    CONSOLE.heading(
        "Builds"
    )
    print()

    print(
        f"{'Build':<10}"
        f"{'Status':<13}"
        f"{'Method':<30}"
        f"{'Arch':<8}"
        f"Output"
    )

    print("-" * 92)

    for manifest_path in manifests:
        try:
            data = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            continue

        method = data.get(
            "method",
            {}
        )

        preset = data.get(
            "preset",
            {}
        )

        output = data.get(
            "output",
            {}
        ) or {}

        status_raw = str(
            data.get(
                "status",
                "?"
            )
        )

        if status_raw == "success":
            status_text = "✓ success"

        elif status_raw == "failed":
            status_text = "✗ failed"

        else:
            status_text = status_raw

        status_field = (
            f"{status_text:<13}"
        )

        if status_raw == "success":
            status = CONSOLE.theme.green(
                status_field
            )

        elif status_raw == "failed":
            status = CONSOLE.theme.red(
                status_field
            )

        else:
            status = status_field

        build_id = str(
            data.get(
                "build_id",
                "?"
            )
        )

        method_id = str(
            method.get(
                "id",
                "?"
            )
        )

        arch = str(
            preset.get(
                "architecture",
                "?"
            )
        )

        output_file = str(
            output.get(
                "file",
                ""
            )
        )

        print(
            f"{build_id:<10}"
            f"{status}"
            f"{method_id:<30}"
            f"{arch:<8}"
            f"{output_file}"
        )

    if (
        not include_all
        and total > len(manifests)
    ):
        print()
        print(
            CONSOLE.theme.dim(
                f"Showing latest {len(manifests)} "
                f"of {total} builds. "
                "Use 'mifa builds --all' "
                "to show everything."
            )
        )


def show_build(
    build_id
):
    data = load_manifest(
        build_id
    )

    print(
        json.dumps(
            data,
            indent=2
        )
    )


def export_report(
    build_id
):
    exporter = ReportExporter(
        ROOT
    )

    result = exporter.export(
        build_id
    )

    print()
    print("[+] Report generated")
    print(
        f"Build copy : {result['build']}"
    )
    print(
        f"Report     : {result['report']}"
    )


def print_result(
    result
):
    manifest = result[
        "manifest"
    ]

    build_dir = result[
        "build_dir"
    ]

    build_id = result[
        "build_id"
    ]

    output = manifest.get(
        "output",
        {}
    )

    output_file = (
        build_dir
        / output.get(
            "file",
            ""
        )
    )

    preflight = None
    preflight_error = None

    try:
        preflight = BuildPreflight(
            ROOT
        ).verify(
            build_id
        )

    except Exception as exc:
        preflight_error = exc

    report = None
    report_error = None

    try:
        report = ReportExporter(
            ROOT
        ).export(
            build_id
        )

    except Exception as exc:
        report_error = exc

    print()

    CONSOLE.success(
        f"Build {build_id}"
    )

    if preflight is None:
        CONSOLE.warning(
            f"Preflight error: "
            f"{preflight_error}"
        )

    elif (
        preflight.get(
            "result"
        ) == "PASS"
    ):
        CONSOLE.success(
            "Preflight passed"
        )

    else:
        CONSOLE.warning(
            "Preflight "
            + str(
                preflight.get(
                    "result",
                    "UNKNOWN"
                )
            )
        )

    CONSOLE.label(
        "Output",
        output_file
    )

    if CONSOLE.verbose:
        print()

        CONSOLE.heading(
            "Build details"
        )

        CONSOLE.label(
            "SHA256",
            output.get(
                "sha256",
                ""
            )
        )

        CONSOLE.label(
            "Manifest",
            build_dir
            / "build.json"
        )

        if preflight is not None:
            roundtrip = preflight[
                "payload_roundtrip"
            ]

            CONSOLE.label(
                "Architecture",
                (
                    f"{preflight['actual_arch']} "
                    f"(expected "
                    f"{preflight['expected_arch']})"
                )
            )

            CONSOLE.label(
                "Hash match",
                preflight[
                    "hash_match"
                ]
            )

            CONSOLE.label(
                "Arch match",
                preflight[
                    "arch_match"
                ]
            )

            CONSOLE.label(
                "Round-trip",
                (
                    "N/A"
                    if roundtrip is None
                    else roundtrip
                )
            )

        if report is not None:
            CONSOLE.label(
                "Report",
                report[
                    "report"
                ]
            )

        elif report_error is not None:
            CONSOLE.warning(
                f"Report error: "
                f"{report_error}"
            )



def interactive_build(
    builder,
    technique=None
):
    if technique is None:
        techniques = builder.registry.discover()

        if not techniques:
            print()
            CONSOLE.warning(
                "No techniques installed."
            )
            return False

        display_names = [
            method["name"].split(
                " (",
                1
            )[0]
            for method in techniques
        ]

        selected_name = choose(
            "Select technique",
            display_names,
        )

        method = next(
            item
            for item in techniques
            if item["name"].split(
                " (",
                1
            )[0] == selected_name
        )

        technique = method[
            "operational"
        ][
            "alias"
        ]

    method = builder.registry.get(
        technique
    )

    if method is None:
        raise ValueError(
            f"Technique not found: {technique}"
        )

    # Current interactive release is intentionally x64-only.
    # Backend architecture support remains unchanged.
    architecture = "x64"

    if architecture not in method.get(
        "architectures",
        []
    ):
        raise ValueError(
            f"{method['name']} does not support x64"
        )

    display_name = method["name"].split(
        " (",
        1
    )[0]

    provider = None
    payload = None
    payload_type = None
    transform = None
    provider_options = {}

    if method.get(
        "requires_payload",
        False
    ):
        providers = method.get(
            "providers",
            []
        )

        if technique == "reflective-dll":
            if "reflective-builtin" not in providers:
                raise ValueError(
                    "Built-in reflective payload "
                    "is not available"
                )

            provider = "reflective-builtin"
            payload = "builtin"

            print()
            CONSOLE.heading(
                display_name
            )
            print()
            print(
                CONSOLE.theme.dim(
                    "Using Mifa built-in reflective DLL"
                )
            )

        else:
            if "msfvenom" not in providers:
                raise ValueError(
                    "msfvenom provider is not "
                    "available for this technique"
                )

            provider = "msfvenom"

            print()
            CONSOLE.heading(
                display_name
            )
            print()

            while True:
                print(
                    CONSOLE.theme.bold(
                        "Payload module"
                    )
                )
                print()
                print(
                    CONSOLE.theme.dim(
                        "  Example: windows/x64/exec"
                    )
                )
                print()

                payload = input(
                    "> "
                ).strip()

                if not payload:
                    print()
                    CONSOLE.error(
                        "Payload module is required"
                    )
                    print()
                    continue

                if any(
                    char.isspace()
                    for char in payload
                ):
                    print()
                    CONSOLE.error(
                        "Payload module must not "
                        "contain whitespace"
                    )
                    print()
                    continue

                if not payload.startswith(
                    "windows/x64/"
                ):
                    print()
                    CONSOLE.error(
                        "Interactive mode currently "
                        "supports Windows x64 payload "
                        "modules only"
                    )
                    print()
                    continue

                break

            contract = method.get(
                "payload_contract",
                {}
            )

            if contract.get(
                "pe_kind"
            ) == "dll":
                msf_format = "dll"
            else:
                msf_format = "raw"

            provider_options.update({
                "architecture": architecture,
                "platform": "windows",
                "format": msf_format,
            })

            while True:
                print()
                print(
                    CONSOLE.theme.bold(
                        "Payload options"
                    )
                )
                print()
                print(
                    CONSOLE.theme.dim(
                        "  Optional msfvenom options"
                    )
                )
                print(
                    CONSOLE.theme.dim(
                        "  Format: KEY=VALUE"
                    )
                )
                print(
                    CONSOLE.theme.dim(
                        "  Multiple options may be "
                        "separated by spaces"
                    )
                )
                print(
                    CONSOLE.theme.dim(
                        '  Quote values with spaces: '
                        'CMD="cmd.exe /c whoami"'
                    )
                )
                print(
                    CONSOLE.theme.dim(
                        "  Press Enter to skip"
                    )
                )
                print()

                option_line = input(
                    "> "
                ).strip()

                if not option_line:
                    msf_options = []
                    break

                try:
                    msf_options = shlex.split(
                        option_line
                    )
                except ValueError as exc:
                    print()
                    CONSOLE.error(
                        f"Invalid option syntax: {exc}"
                    )
                    continue

                invalid = [
                    item
                    for item in msf_options
                    if (
                        "=" not in item
                        or not item.split(
                            "=",
                            1
                        )[0].strip()
                        or not item.split(
                            "=",
                            1
                        )[1]
                    )
                ]

                if invalid:
                    print()
                    CONSOLE.error(
                        "Each option must use "
                        "KEY=VALUE syntax"
                    )
                    continue

                break

            provider_options[
                "msf_options"
            ] = msf_options

        contract = method.get(
            "payload_contract",
            {}
        )

        payload_types = contract.get(
            "types",
            []
        )

        if len(payload_types) == 1:
            payload_type = payload_types[0]

        elif payload_types:
            payload_type = choose(
                "Payload type",
                payload_types,
            )

        transforms = contract.get(
            "transforms",
            ["copy"],
        )

        transform = (
            transforms[0]
            if len(transforms) == 1
            else choose(
                "Payload transform",
                transforms,
            )
        )

    print()
    CONSOLE.heading(
        "Build Review"
    )
    print()

    CONSOLE.label(
        "Technique",
        display_name
    )

    CONSOLE.label(
        "Architecture",
        architecture
    )

    if method.get(
        "requires_payload",
        False
    ):
        if provider == "reflective-builtin":
            CONSOLE.label(
                "Payload",
                "Built-in reflective DLL"
            )

        else:
            CONSOLE.label(
                "Payload",
                payload
            )

            option_keys = [
                item.split(
                    "=",
                    1
                )[0]
                for item in provider_options.get(
                    "msf_options",
                    []
                )
            ]

            if option_keys:
                redacted = ", ".join(
                    f"{key}=<redacted>"
                    for key in option_keys
                )

                CONSOLE.label(
                    "Options",
                    redacted
                )

            else:
                CONSOLE.label(
                    "Options",
                    "none"
                )

    if CONSOLE.verbose:
        CONSOLE.label(
            "Payload type",
            payload_type
        )

        CONSOLE.label(
            "Transform",
            transform
        )

    confirm = input(
        "\nBuild artifact? [Y/n] > "
    ).strip().lower()

    if confirm not in {
        "",
        "y",
        "yes",
    }:
        CONSOLE.warning(
            "Build cancelled"
        )
        return False

    result = builder.build(
        technique=technique,
        architecture=architecture,
        payload_source=payload,
        provider_id=(
            provider
            or "file"
        ),
        payload_type=payload_type,
        transform=transform,
        build_type="release",
        provider_options=provider_options,
    )

    print_result(
        result
    )

    return True

def interactive_builds():
    while True:
        print()
        show_builds()

        build_id = input(
            "\nBuild ID "
            "[Enter to go back]:\n> "
        ).strip()

        if not build_id:
            return

        try:
            load_manifest(
                build_id
            )

        except Exception as exc:
            print(
                f"\n[!] {exc}"
            )
            continue

        while True:
            print()
            print(
                f"Build {build_id}"
            )
            print("-" * 46)
            print("[1] Preflight")
            print("[2] Report")
            print("[3] Details")
            print("[0] Back")

            selection = input(
                "\n> "
            ).strip()

            try:
                if selection == "1":
                    result = BuildPreflight(
                        ROOT
                    ).verify(
                        build_id
                    )

                    roundtrip = result[
                        "payload_roundtrip"
                    ]

                    print()
                    print("Preflight")
                    print("-" * 46)

                    print(
                        f"Status      : "
                        f"{result['status']}"
                    )

                    print(
                        f"Hash match  : "
                        f"{result['hash_match']}"
                    )

                    print(
                        f"Architecture: "
                        f"{result['actual_arch']} "
                        f"(expected "
                        f"{result['expected_arch']})"
                    )

                    print(
                        f"Arch match  : "
                        f"{result['arch_match']}"
                    )

                    print(
                        "Round-trip  : "
                        + (
                            "N/A"
                            if roundtrip is None
                            else str(roundtrip)
                        )
                    )

                    print(
                        f"Result      : "
                        f"{result['result']}"
                    )

                elif selection == "2":
                    export_report(
                        build_id
                    )

                elif selection == "3":
                    show_build(
                        build_id
                    )

                elif selection == "0":
                    break

                else:
                    print(
                        "\nInvalid selection."
                    )

            except Exception as exc:
                print(
                    f"\n[!] {exc}"
                )


def interactive_menu():
    builder = OperationalBuilder(
        ROOT
    )

    banner()

    while True:
        techniques = (
            builder.registry.discover()
        )

        if not techniques:
            CONSOLE.warning(
                "No techniques installed."
            )
            return 0

        print()
        CONSOLE.heading(
            "Select technique"
        )
        print()

        for index, method in enumerate(
            techniques,
            start=1,
        ):
            display_name = method[
                "name"
            ].split(
                " (",
                1
            )[0]

            print(
                f"  "
                f"{CONSOLE.theme.cyan(index)}  "
                f"{display_name}"
            )

        print()
        print(
            "  "
            + CONSOLE.theme.dim(
                "q  Exit"
            )
        )

        selection = input(
            "\n> "
        ).strip().lower()

        if selection in {
            "q",
            "quit",
            "exit",
        }:
            return 0

        try:
            index = int(
                selection
            ) - 1

        except ValueError:
            print()
            CONSOLE.error(
                "Invalid selection"
            )
            input(
                "\nPress Enter to continue..."
            )
            continue

        if not (
            0 <= index < len(techniques)
        ):
            print()
            CONSOLE.error(
                "Invalid selection"
            )
            input(
                "\nPress Enter to continue..."
            )
            continue

        method = techniques[
            index
        ]

        readiness = readiness_for(
            method
        )

        if not readiness[
            "buildable"
        ]:
            print()

            CONSOLE.warning(
                f"{method['name']} "
                "is not available yet."
            )

            input(
                "\nPress Enter to continue..."
            )
            continue

        try:
            completed = interactive_build(
                builder,
                technique=method[
                    "operational"
                ][
                    "alias"
                ],
            )

            if completed is False:
                continue

        except Exception as exc:
            print()
            CONSOLE.error(
                str(exc)
            )

        input(
            "\nPress Enter to continue..."
        )

def build_parser():
    parser = argparse.ArgumentParser(
        prog="mifa",
        description=(
            "Mifa - operational payload "
            "build utility"
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )

    build = sub.add_parser(
        "build",
    help="Build an operational technique"
    )

    build.add_argument(
        "--technique",
        required=True,
    )

    build.add_argument(
        "--payload",
    )

    build.add_argument(
        "--arch",
        choices=[
            "x64",
            "x86",
        ],
        required=True,
    )

    build.add_argument(
        "--provider",
        default="file",
    )

    build.add_argument(
        "--producer",
    )

    build.add_argument(
        "--msf-format",
        choices=[
            "raw",
            "dll",
            "exe",
        ],
    )

    build.add_argument(
        "--msf-option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
    )

    build.add_argument(
        "--payload-type",
    )

    build.add_argument(
        "--transform",
    )





    build.add_argument(
        "--build-type",
        choices=[
            "release",
            "debug",
        ],
        default="release",
    )

    build.add_argument(
        "--set",
        action="append",
        default=[],
    )

    techniques = sub.add_parser(
        "techniques",
    help="List available techniques"
    )

    techniques.add_argument(
        "--all",
        action="store_true",
        dest="include_hidden",
    )

    builds = sub.add_parser(
        "builds",
        help="List recent builds",
    )

    builds.add_argument(
        "--all",
        action="store_true",
        dest="include_all",
        help="Show all recorded builds",
    )

    show = sub.add_parser(
        "show",
    help="Show build manifest"
    )

    show.add_argument(
        "build_id"
    )

    report = sub.add_parser(
        "report",
    help="Export build report"
    )

    report.add_argument(
        "build_id"
    )

    sub.add_parser(
        "payloads",
    help="List payload providers"
    )

    preflight = sub.add_parser(
        "preflight",
    help="Verify a completed build"
    )

    preflight.add_argument(
        "build_id"
    )

    return parser


def main():
    parser = build_parser()

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed build output",
    )

    # Allow global UI flags before or after
    # the selected subcommand.
    ui_flags = []
    cli_args = []

    for item in sys.argv[1:]:
        if item in {
            "--no-color",
            "--verbose",
            "-v",
        }:
            ui_flags.append(
                item
            )
        else:
            cli_args.append(
                item
            )

    args = parser.parse_args(
        ui_flags
        + cli_args
    )

    configure_console(
        color=not args.no_color,
        verbose=args.verbose,
    )

    # No subcommand means interactive mode.
    # Global UI flags still configure the session.
    if args.command is None:
        return interactive_menu()

    builder = OperationalBuilder(
        ROOT
    )

    if args.command == "techniques":
        show_techniques(
            builder.registry,
            include_hidden=args.include_hidden,
        )
        return 0

    if args.command == "builds":
        show_builds(
            include_all=args.include_all
        )
        return 0

    if args.command == "show":
        try:
            show_build(
                args.build_id
            )
            return 0

        except Exception as exc:
            print(
                f"[!] {exc}"
            )
            return 1

    if args.command == "report":
        try:
            export_report(
                args.build_id
            )
            return 0

        except Exception as exc:
            print(
                f"[!] {exc}"
            )
            return 1

    if args.command == "preflight":
        try:
            result = BuildPreflight(
                ROOT
            ).verify(
                args.build_id
            )

            print()

            if result["result"] == "PASS":
                CONSOLE.success(
                    f"Preflight "
                    f"{result['build_id']} passed"
                )
            else:
                CONSOLE.error(
                    f"Preflight "
                    f"{result['build_id']} failed"
                )

            CONSOLE.label(
                "Artifact",
                result[
                    "artifact"
                ]
            )

            if CONSOLE.verbose:
                print()

                CONSOLE.heading(
                    "Preflight details"
                )

                CONSOLE.label(
                    "Status",
                    result[
                        "status"
                    ]
                )

                CONSOLE.label(
                    "Hash match",
                    result[
                        "hash_match"
                    ]
                )

                CONSOLE.label(
                    "Architecture",
                    (
                        f"{result['actual_arch']} "
                        f"(expected "
                        f"{result['expected_arch']})"
                    )
                )

                CONSOLE.label(
                    "Arch match",
                    result[
                        "arch_match"
                    ]
                )

                roundtrip = result[
                    "payload_roundtrip"
                ]

                CONSOLE.label(
                    "Round-trip",
                    (
                        "N/A"
                        if roundtrip is None
                        else roundtrip
                    )
                )

            return (
                0
                if result["result"] == "PASS"
                else 1
            )

        except Exception as exc:
            CONSOLE.error(
                str(exc)
            )
            return 1

    if args.command == "payloads":
        for provider in list_providers():
            print(
                provider
            )

        return 0

    if args.command == "build":
        provider_options = {}


        if args.producer:
            provider_options[
                "producer"
            ] = args.producer

        if args.provider == "msfvenom":
            method = builder.registry.get(
                args.technique
            )

            contract = (
                method.get(
                    "payload_contract",
                    {}
                )
                if method
                else {}
            )

            msf_format = args.msf_format

            if msf_format is None:
                if (
                    contract.get(
                        "pe_kind"
                    ) == "dll"
                ):
                    msf_format = "dll"
                else:
                    msf_format = "raw"

            provider_options[
                "architecture"
            ] = args.arch

            provider_options[
                "platform"
            ] = "windows"

            provider_options[
                "format"
            ] = msf_format

            provider_options[
                "msf_options"
            ] = list(
                args.msf_option
                or []
            )

        try:
            result = builder.build(
                technique=args.technique,
                architecture=args.arch,
                payload_source=args.payload,
                provider_id=args.provider,
                payload_type=args.payload_type,
                transform=args.transform,
                build_type=args.build_type,
                cli_parameters=args.set,
                provider_options=provider_options,
            )

        except Exception as exc:
            print(
                f"[!] Build failed: {exc}"
            )
            return 1

        print_result(
            result
        )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
