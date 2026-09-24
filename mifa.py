#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from core.operational_builder import OperationalBuilder
from core.techniques import TechniqueRegistry


ROOT = Path(__file__).resolve().parent


def banner():
    print()
    print("Mifa")
    print("=" * 44)
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


def show_techniques(
    registry
):
    techniques = registry.discover()

    if not techniques:
        print("No operational techniques available.")
        return

    print()
    print(
        f"{'Alias':<16}"
        f"{'Category':<18}"
        f"{'Runtime':<12}"
        f"Architectures"
    )

    print("-" * 66)

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

        print(
            f"{operational['alias']:<16}"
            f"{operational['category']:<18}"
            f"{operational['runtime']:<12}"
            f"{architectures}"
        )


def show_builds():
    builds_dir = ROOT / "builds"

    manifests = sorted(
        builds_dir.glob(
            "K-*/build.json"
        ),
        reverse=True,
    )

    if not manifests:
        print("No builds found.")
        return

    print()

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

        print(
            f"{data.get('build_id', '?'):<10} "
            f"{data.get('status', '?'):<10} "
            f"{method.get('id', '?'):<22} "
            f"{preset.get('architecture', '?')}"
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
        print(
            "No operational techniques available."
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

    architectures = method.get(
        "architectures",
        []
    )

    architecture = choose(
        "\nArchitecture:",
        architectures,
    )

    print()
    print("Payload source:")
    print("[1] Existing file")

    while True:
        selection = input("> ").strip()

        if selection == "1":
            provider = "file"
            break

        print("Invalid selection")

    print()
    payload = input(
        "Payload path:\n> "
    ).strip()

    payload_types = method.get(
        "payload_contract",
        {}
    ).get(
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

    transforms = method.get(
        "payload_contract",
        {}
    ).get(
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
    print("Configuration")
    print("-" * 44)
    print(
        f"Technique    : {technique}"
    )
    print(
        f"Architecture : {architecture}"
    )
    print(
        f"Provider     : {provider}"
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
        print("Build cancelled.")
        return

    result = builder.build(
        technique=technique,
        architecture=architecture,
        payload_source=payload,
        provider_id=provider,
        payload_type=payload_type,
        transform=transform,
        build_type="release",
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
        print("[0] Exit")

        selection = input(
            "\n> "
        ).strip()

        if selection == "1":
            try:
                interactive_build(
                    builder
                )
            except Exception as exc:
                print(
                    f"\n[!] {exc}"
                )

            input(
                "\nPress Enter to continue..."
            )

        elif selection == "2":
            print()
            print(
                "Available payload providers:"
            )
            print("file")

            input(
                "\nPress Enter to continue..."
            )

        elif selection == "3":
            show_techniques(
                builder.registry
            )

            input(
                "\nPress Enter to continue..."
            )

        elif selection == "4":
            show_builds()

            input(
                "\nPress Enter to continue..."
            )

        elif selection == "5":
            print()
            print(
                "Report export will be added "
                "in the next milestone."
            )

            input(
                "\nPress Enter to continue..."
            )

        elif selection == "0":
            return 0

        else:
            print(
                "\nInvalid selection."
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

    sub.add_parser(
        "techniques"
    )

    sub.add_parser(
        "builds"
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
            builder.registry
        )
        return 0

    if args.command == "builds":
        show_builds()
        return 0

    if args.command == "build":
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
