#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from core.operational_builder import OperationalBuilder
from core.reporting import ReportExporter
from providers import list_providers


ROOT = Path(__file__).resolve().parent


def banner():
    print()
    print("Mifa")
    print("=" * 46)
    print("Kali-side Operational Build Framework")
    print()


def choose(
    title,
    options
):
    print(title)

    for index, option in enumerate(
        options,
        start=1
    ):
        print(
            f"[{index}] {option}"
        )

    while True:
        value = input("> ").strip()

        try:
            index = int(value) - 1

        except ValueError:
            print("Invalid selection")
            continue

        if 0 <= index < len(options):
            return options[index]

        print("Invalid selection")


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

        if not include_hidden:
            print(
                "Use 'techniques --all' to "
                "include internal pipeline methods."
            )

        return

    print()
    print(
        f"{'Alias':<16}"
        f"{'Category':<18}"
        f"{'Runtime':<12}"
        f"{'State':<10}"
        f"Architectures"
    )

    print("-" * 78)

    for method in techniques:
        operational = method[
            "operational"
        ]

        architectures = ", ".join(
            method.get(
                "architectures",
                []
            )
        )

        state = (
            "internal"
            if operational.get(
                "hidden",
                False
            )
            else "visible"
        )

        print(
            f"{operational['alias']:<16}"
            f"{operational['category']:<18}"
            f"{operational['runtime']:<12}"
            f"{state:<10}"
            f"{architectures}"
        )


def show_builds():
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
        print(
            "No builds found."
        )
        return

    print()
    print(
        f"{'Build':<10}"
        f"{'Status':<10}"
        f"{'Method':<24}"
        f"{'Arch':<8}"
        f"Output"
    )

    print("-" * 84)

    for path in manifests:
        try:
            data = json.loads(
                path.read_text(
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

        print(
            f"{data.get('build_id', '?'):<10}"
            f"{data.get('status', '?'):<10}"
            f"{method.get('id', '?'):<24}"
            f"{preset.get('architecture', '?'):<8}"
            f"{output.get('file', '')}"
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

    print()
    print("[+] Build completed")
    print(
        f"Build ID : "
        f"{result['build_id']}"
    )
    print(
        f"Output   : "
        f"{output_file}"
    )
    print(
        f"SHA256   : "
        f"{output.get('sha256', '')}"
    )
    print(
        f"Manifest : "
        f"{build_dir / 'build.json'}"
    )


def interactive_build(
    builder
):
    techniques = (
        builder.registry.discover()
    )

    if not techniques:
        print()
        print(
            "No user-facing operational "
            "techniques are installed yet."
        )
        return

    aliases = [
        method[
            "operational"
        ][
            "alias"
        ]
        for method in techniques
    ]

    technique = choose(
        "\nTechnique:",
        aliases,
    )

    method = builder.registry.get(
        technique
    )

    architecture = choose(
        "\nArchitecture:",
        method.get(
            "architectures",
            []
        ),
    )

    providers = method.get(
        "providers",
        []
    )

    provider = choose(
        "\nPayload provider:",
        providers,
    )

    print()
    payload = input(
        "Payload path:\n> "
    ).strip()

    provider_options = {}

    if provider == "external":
        producer = input(
            "\nExternal producer name:\n> "
        ).strip()

        provider_options[
            "producer"
        ] = (
            producer
            or "external"
        )

    contract = method.get(
        "payload_contract",
        {}
    )

    payload_types = contract.get(
        "types",
        []
    )

    payload_type = None

    if len(payload_types) == 1:
        payload_type = payload_types[0]

    elif payload_types:
        payload_type = choose(
            "\nPayload type:",
            payload_types,
        )

    transforms = contract.get(
        "transforms",
        [
            "copy"
        ],
    )

    transform = (
        transforms[0]
        if len(transforms) == 1
        else choose(
            "\nPayload transform:",
            transforms,
        )
    )

    print()
    print("Resolved Configuration")
    print("-" * 46)
    print(
        f"Technique    : {technique}"
    )
    print(
        f"Architecture : {architecture}"
    )
    print(
        f"Provider     : {provider}"
    )

    if provider_options.get(
        "producer"
    ):
        print(
            f"Producer     : "
            f"{provider_options['producer']}"
        )

    print(
        f"Payload      : {payload}"
    )
    print(
        f"Payload type : {payload_type}"
    )
    print(
        f"Transform    : {transform}"
    )

    confirm = input(
        "\nBuild? [Y/n]\n> "
    ).strip().lower()

    if confirm not in {
        "",
        "y",
        "yes",
    }:
        print(
            "Build cancelled."
        )
        return

    result = builder.build(
        technique=technique,
        architecture=architecture,
        payload_source=payload,
        provider_id=provider,
        payload_type=payload_type,
        transform=transform,
        build_type="release",
        provider_options=provider_options,
    )

    print_result(
        result
    )


def interactive_menu():
    builder = OperationalBuilder(
        ROOT
    )

    while True:
        banner()

        print("[1] Build")
        print("[2] Payloads")
        print("[3] Techniques")
        print("[4] Builds")
        print("[5] Report")
        print("[6] Show Build")
        print("[0] Exit")

        selection = input(
            "\n> "
        ).strip()

        try:
            if selection == "1":
                interactive_build(
                    builder
                )

            elif selection == "2":
                print()
                print(
                    "Payload providers:"
                )

                for provider in list_providers():
                    print(
                        f"- {provider}"
                    )

                print()
                print(
                    "external imports an artifact "
                    "already produced by another tool."
                )

            elif selection == "3":
                show_techniques(
                    builder.registry
                )

            elif selection == "4":
                show_builds()

            elif selection == "5":
                build_id = input(
                    "\nBuild ID:\n> "
                ).strip()

                export_report(
                    build_id
                )

            elif selection == "6":
                build_id = input(
                    "\nBuild ID:\n> "
                ).strip()

                show_build(
                    build_id
                )

            elif selection == "0":
                return 0

            else:
                print(
                    "\nInvalid selection."
                )

        except Exception as exc:
            print(
                f"\n[!] {exc}"
            )

        if selection != "0":
            input(
                "\nPress Enter to continue..."
            )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Mifa operational build framework"
        )
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    build = sub.add_parser(
        "build"
    )

    build.add_argument(
        "--technique",
        required=True,
    )

    build.add_argument(
        "--payload",
        required=True,
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
        "techniques"
    )

    techniques.add_argument(
        "--all",
        action="store_true",
        dest="include_hidden",
    )

    sub.add_parser(
        "builds"
    )

    show = sub.add_parser(
        "show"
    )

    show.add_argument(
        "build_id"
    )

    report = sub.add_parser(
        "report"
    )

    report.add_argument(
        "build_id"
    )

    sub.add_parser(
        "payloads"
    )

    return parser


def main():
    parser = build_parser()

    if len(
        sys.argv
    ) == 1:
        return interactive_menu()

    args = parser.parse_args()

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
        show_builds()
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
