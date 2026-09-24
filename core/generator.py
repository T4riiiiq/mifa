from pathlib import Path
import re


class SourceGenerator:
    UNRESOLVED_PARAMETER = re.compile(
        r"\{\{PARAM_[A-Z0-9_]+\}\}"
    )

    def _render(
        self,
        template,
        values
    ):
        generated = template

        for key, value in values.items():
            generated = generated.replace(
                key,
                str(value)
            )

        unresolved = (
            self.UNRESOLVED_PARAMETER.findall(
                generated
            )
        )

        if unresolved:
            unique = sorted(
                set(
                    unresolved
                )
            )

            raise ValueError(
                "Unresolved parameter token(s): "
                + ", ".join(
                    unique
                )
            )

        return generated

    def _escape_c_string(
        self,
        value
    ):
        return (
            str(value)
            .replace(
                "\\",
                "\\\\"
            )
            .replace(
                "\"",
                "\\\""
            )
            .replace(
                "\n",
                "\\n"
            )
            .replace(
                "\r",
                "\\r"
            )
            .replace(
                "\t",
                "\\t"
            )
        )

    def _parameter_value(
        self,
        value,
        spec
    ):
        if value is None:
            return ""

        render = spec.get(
            "render",
            "raw"
        )

        if render == "c_string":
            return self._escape_c_string(
                value
            )

        if isinstance(
            value,
            bool
        ):
            return (
                "true"
                if value
                else "false"
            )

        return str(
            value
        )

    def _parameter_tokens(
        self,
        method,
        parameters
    ):
        values = {}

        specs = method.get(
            "parameters",
            {}
        )

        for name, spec in specs.items():
            token = (
                "{{PARAM_"
                + name.upper()
                + "}}"
            )

            values[token] = (
                self._parameter_value(
                    parameters.get(
                        name
                    ),
                    spec
                )
            )

        return values

    def generate(
        self,
        method,
        preset,
        build_id,
        build_dir,
        payload_info=None,
        payload_type=None,
        parameters=None
    ):
        method_path = Path(
            method["_path"]
        )

        values = {
            "{{BUILD_ID}}":
                build_id,

            "{{ARCH}}":
                preset.get(
                    "architecture",
                    ""
                ),

            "{{BUILD_TYPE}}":
                preset.get(
                    "build_type",
                    ""
                ),

            "{{PAYLOAD_NAME}}":
                "",

            "{{PAYLOAD_TYPE}}":
                "",

            "{{PAYLOAD_SIZE}}":
                "",

            "{{PAYLOAD_SHA256}}":
                "",

            "{{PAYLOAD_TRANSFORM}}":
                "",

            "{{PAYLOAD_SOURCE_NAME}}":
                "",

            "{{PAYLOAD_SOURCE_SIZE}}":
                "",

            "{{PAYLOAD_SOURCE_SHA256}}":
                "",

            "{{PAYLOAD_STAGED_NAME}}":
                "",

            "{{PAYLOAD_STAGED_SIZE}}":
                "",

            "{{PAYLOAD_STAGED_SHA256}}":
                ""
        }

        if payload_info is not None:
            values.update({
                "{{PAYLOAD_NAME}}":
                    payload_info.get(
                        "name",
                        ""
                    ),

                "{{PAYLOAD_TYPE}}":
                    payload_type or "",

                "{{PAYLOAD_SIZE}}":
                    str(
                        payload_info.get(
                            "size_bytes",
                            ""
                        )
                    ),

                "{{PAYLOAD_SHA256}}":
                    payload_info.get(
                        "sha256",
                        ""
                    ),

                "{{PAYLOAD_TRANSFORM}}":
                    payload_info.get(
                        "transform",
                        "copy"
                    ),

                "{{PAYLOAD_SOURCE_NAME}}":
                    payload_info.get(
                        "source",
                        {}
                    ).get(
                        "name",
                        ""
                    ),

                "{{PAYLOAD_SOURCE_SIZE}}":
                    str(
                        payload_info.get(
                            "source",
                            {}
                        ).get(
                            "size_bytes",
                            ""
                        )
                    ),

                "{{PAYLOAD_SOURCE_SHA256}}":
                    payload_info.get(
                        "source",
                        {}
                    ).get(
                        "sha256",
                        ""
                    ),

                "{{PAYLOAD_STAGED_NAME}}":
                    payload_info.get(
                        "staged",
                        {}
                    ).get(
                        "name",
                        ""
                    ),

                "{{PAYLOAD_STAGED_SIZE}}":
                    str(
                        payload_info.get(
                            "staged",
                            {}
                        ).get(
                            "size_bytes",
                            ""
                        )
                    ),

                "{{PAYLOAD_STAGED_SHA256}}":
                    payload_info.get(
                        "staged",
                        {}
                    ).get(
                        "sha256",
                        ""
                    )
            })

        values.update(
            self._parameter_tokens(
                method=method,
                parameters=parameters or {}
            )
        )

        source_dir = (
            build_dir / "source"
        )

        source_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        generated_files = []

        for source in method.get(
            "sources",
            []
        ):
            template_path = (
                method_path
                / source["template"]
            )

            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template not found: "
                    f"{template_path}"
                )

            template = (
                template_path.read_text(
                    encoding="utf-8"
                )
            )

            generated = self._render(
                template,
                values
            )

            output_path = (
                source_dir
                / source["output"]
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            output_path.write_text(
                generated,
                encoding="utf-8"
            )

            generated_files.append({
                "path":
                    output_path,

                "compile":
                    source["compile"]
            })

        return generated_files
