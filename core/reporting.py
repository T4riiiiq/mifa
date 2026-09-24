from pathlib import Path
import json
import re
import shlex


class ReportExporter:
    BUILD_ID = re.compile(
        r"^K-\d{4}$"
    )

    def __init__(
        self,
        root: Path
    ):
        self.root = Path(root)

        self.builds_dir = (
            self.root
            / "builds"
        )

        self.reports_dir = (
            self.root
            / "reports"
        )

        self.reports_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def load(
        self,
        build_id
    ):
        if not self.BUILD_ID.match(
            build_id
        ):
            raise ValueError(
                f"Invalid build ID: {build_id}"
            )

        manifest = (
            self.builds_dir
            / build_id
            / "build.json"
        )

        if not manifest.exists():
            raise FileNotFoundError(
                f"Build not found: {build_id}"
            )

        return json.loads(
            manifest.read_text(
                encoding="utf-8"
            )
        )

    def render(
        self,
        build_id
    ):
        data = self.load(
            build_id
        )

        method = data.get(
            "method",
            {}
        )

        preset = data.get(
            "preset",
            {}
        )

        payload = data.get(
            "payload"
        ) or {}

        provider = payload.get(
            "provider"
        ) or {}

        source = payload.get(
            "source"
        ) or {}

        staged = payload.get(
            "staged"
        ) or {}

        compiler = data.get(
            "compiler"
        ) or {}

        output = data.get(
            "output"
        ) or {}

        command = compiler.get(
            "command",
            []
        )

        if isinstance(
            command,
            list
        ):
            command_text = shlex.join(
                str(item)
                for item in command
            )
        else:
            command_text = str(
                command
            )

        lines = [
            "# Mifa Build Report",
            "",
            f"**Build ID:** {data.get('build_id', '')}",
            "",
            f"**Status:** {data.get('status', '')}",
            "",
            f"**Created:** {data.get('created_at', '')}",
            "",
            f"**Completed:** {data.get('completed_at', '')}",
            "",
            "## Build Configuration",
            "",
            f"- Method: `{method.get('id', '')}`",
            f"- Name: {method.get('name', '')}",
            f"- Language: `{method.get('language', '')}`",
            f"- Architecture: `{preset.get('architecture', '')}`",
            f"- Build type: `{preset.get('build_type', '')}`",
            "",
            "## Payload Provenance",
            "",
            f"- Provider: `{provider.get('provider', '')}`",
        ]

        if provider.get(
            "producer"
        ):
            lines.append(
                f"- Producer: `{provider['producer']}`"
            )

        lines.extend([
            f"- Type: `{payload.get('type', '')}`",
            f"- Transform: `{payload.get('transform', '')}`",
            f"- Source name: `{source.get('name', '')}`",
            f"- Source size: {source.get('size_bytes', '')}",
            f"- Source SHA256: `{source.get('sha256', '')}`",
            f"- Staged file: `{staged.get('file', '')}`",
            f"- Staged SHA256: `{staged.get('sha256', '')}`",
            "",
            "## Compilation",
            "",
            f"- Compiler: `{compiler.get('name', '')}`",
            "",
            "~~~text",
            command_text,
            "~~~",
            "",
            "## Output",
            "",
            f"- File: `{output.get('file', '')}`",
            f"- Size: {output.get('size_bytes', '')}",
            f"- SHA256: `{output.get('sha256', '')}`",
            "",
        ])

        return "\n".join(
            lines
        )

    def export(
        self,
        build_id
    ):
        report = self.render(
            build_id
        )

        build_report = (
            self.builds_dir
            / build_id
            / "REPORT.md"
        )

        central_report = (
            self.reports_dir
            / f"{build_id}.md"
        )

        build_report.write_text(
            report,
            encoding="utf-8"
        )

        central_report.write_text(
            report,
            encoding="utf-8"
        )

        return {
            "build": build_report,
            "report": central_report,
        }
