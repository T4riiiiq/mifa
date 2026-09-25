#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from core.operational_builder import OperationalBuilder
from core.preflight import BuildPreflight
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

        return

    print()
    print(
        f"{'Alias':<16}"
        f"{'Category':<18}"
        f"{'Runtime':<12}"
        f"{'Validation':<18}"
        f"Architectures"
    )

    print("-" * 90)

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

        validation = operational.get(
            "validation",
            "?"
        )

        print(
            f"{operational['alias']:<16}"
            f"{operational['category']:<18}"
            f"{operational['runtime']:<12}"
            f"{validation:<18}"
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

    print()
    print("[+] Build completed")
    print(
        f"Build ID : {build_id}"
    )
    print(
        f"Output   : {output_file}"
    )
    print(
        f"SHA256   : "
        f"{output.get('sha256', '')}"
    )
    print(
        f"Manifest : "
        f"{build_dir / 'build.json'}"
    )

    print()
    print("Preflight")
    print("-" * 46)

    try:
        preflight = BuildPreflight(
            ROOT
        ).verify(
            build_id
        )

        roundtrip = preflight[
            "payload_roundtrip"
        ]

        print(
            f"Hash match  : "
            f"{preflight['hash_match']}"
        )

        print(
            f"Architecture: "
            f"{preflight['actual_arch']} "
            f"(expected "
            f"{preflight['expected_arch']})"
        )

        print(
            f"Arch match  : "
            f"{preflight['arch_match']}"
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
            f"{preflight['result']}"
        )

    except Exception as exc:
        print(
            f"Preflight   : ERROR ({exc})"
        )

    print()
    print("Report")
    print("-" * 46)

    try:
        exporter = ReportExporter(
            ROOT
        )

        report = exporter.export(
            build_id
        )

        print(
            f"Build copy : "
            f"{report['build']}"
        )

        print(
            f"Report     : "
            f"{report['report']}"
        )

    except Exception as exc:
        print(
            f"Report     : ERROR ({exc})"
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

    provider = None
    payload = None
    payload_type = None
    transform = None
    provider_options = {}
    pipeline_options = {}

    if method.get(
        "requires_payload",
        False
    ):
        providers = method.get(
            "providers",
            []
        )

        provider_labels = {
            "file":
                "Existing file",

            "external":
                "External artifact",
        }

        display_providers = [
            provider_labels.get(
                item,
                item
            )
            for item in providers
        ]

        selected_provider = choose(
            "\nPayload:",
            display_providers,
        )

        provider = next(
            item
            for item in providers
            if provider_labels.get(
                item,
                item
            ) == selected_provider
        )

        print()
        payload = input(
            "File path:\n> "
        ).strip()

        if provider == "external":
            producer = input(
                "\nProducer name [optional]:\n> "
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

    if method.get(
        "requires_payload",
        False
    ):
        crypto_transform = choose(
            "\nTransform:",
            [
                "none",
                "xor",
                "aes-256-cbc",
                "aes-256-gcm",
            ],
        )

        encoding = choose(
            "\nEncoding:",
            [
                "none",
                "base64",
                "hex",
            ],
        )

        compression = choose(
            "\nCompression:",
            [
                "none",
                "gzip",
                "deflate",
            ],
        )

        pipeline_options = {
            "transform":
                crypto_transform,

            "encoding":
                encoding,

            "compression":
                compression,
        }

    runtime_arguments = method.get(
        "runtime_arguments",
        []
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

    if method.get(
        "requires_payload",
        False
    ):
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

        print(
            "Processing   : "
            f"{pipeline_options.get('transform', 'none')} / "
            f"{pipeline_options.get('encoding', 'none')} / "
            f"{pipeline_options.get('compression', 'none')}"
        )

    else:
        print(
            "Payload      : not required"
        )

    if runtime_arguments:
        print()
        print("Runtime Arguments")

        for argument in runtime_arguments:
            requirement = (
                "required"
                if argument.get(
                    "required",
                    True
                )
                else "optional"
            )

            print(
                f"- {argument.get('name')} "
                f"({argument.get('type')}, "
                f"{requirement})"
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
        provider_id=(
            provider
            or "file"
        ),
        payload_type=payload_type,
        transform=transform,
        build_type="release",
        provider_options=provider_options,
        pipeline_options=pipeline_options,
    )

    print_result(
        result
    )


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

    while True:
        banner()

        print("[1] Build")
        print("[2] Builds")
        print("[3] Techniques")
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
                interactive_builds()

            elif selection == "3":
                show_techniques(
                    builder.registry
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
        "--crypto",
        choices=[
            "none",
            "xor",
            "aes-256-cbc",
            "aes-256-gcm",
        ],
        default="none",
    )

    build.add_argument(
        "--encoding",
        choices=[
            "none",
            "base64",
            "hex",
        ],
        default="none",
    )

    build.add_argument(
        "--compression",
        choices=[
            "none",
            "gzip",
            "deflate",
        ],
        default="none",
    )

    build.add_argument(
        "--key-hex",
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

    preflight = sub.add_parser(
        "preflight"
    )

    preflight.add_argument(
        "build_id"
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

    if args.command == "preflight":
        try:
            result = BuildPreflight(
                ROOT
            ).verify(
                args.build_id
            )

            print()
            print("Preflight")
            print("-" * 46)

            print(
                f"Build       : "
                f"{result['build_id']}"
            )

            print(
                f"Status      : "
                f"{result['status']}"
            )

            print(
                f"Artifact    : "
                f"{result['artifact']}"
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

            roundtrip = result[
                "payload_roundtrip"
            ]

            print(
                "Round-trip  : "
                + (
                    "N/A"
                    if roundtrip is None
                    else str(roundtrip)
                )
            )

            print()
            print(
                f"Result      : "
                f"{result['result']}"
            )

            return (
                0
                if result["result"] == "PASS"
                else 1
            )

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

        pipeline_options = {
            "transform":
                args.crypto,

            "encoding":
                args.encoding,

            "compression":
                args.compression,

            "key_hex":
                args.key_hex,
        }

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
                pipeline_options=pipeline_options,
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
