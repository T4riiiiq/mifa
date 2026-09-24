from pathlib import Path

from core.builds import BuildManager
from core.compatibility import CompatibilityChecker
from core.compiler import Compiler
from core.generator import SourceGenerator
from core.parameters import ParameterResolver
from core.payloads import PayloadManager
from core.schema import MethodSchemaValidator
from core.techniques import TechniqueRegistry
from providers import get_provider


class OperationalBuilder:
    def __init__(
        self,
        root: Path
    ):
        self.root = Path(root)

        self.registry = TechniqueRegistry(
            self.root / "techniques"
        )

        self.builds = BuildManager(
            self.root / "builds"
        )

        self.schema = MethodSchemaValidator()
        self.compatibility = CompatibilityChecker()
        self.compiler = Compiler()
        self.generator = SourceGenerator()
        self.parameters = ParameterResolver()
        self.payloads = PayloadManager()

    def build(
        self,
        technique,
        architecture,
        payload_source=None,
        provider_id="file",
        payload_type=None,
        transform=None,
        build_type="release",
        cli_parameters=None,
        provider_options=None
    ):
        method = self.registry.get(
            technique
        )

        if method is None:
            raise ValueError(
                f"Unknown operational technique: "
                f"{technique}"
            )

        schema_errors = self.schema.validate(
            method
        )

        if schema_errors:
            raise ValueError(
                "; ".join(
                    schema_errors
                )
            )

        operational = method[
            "operational"
        ]

        if not operational.get(
            "deployable",
            False
        ):
            raise ValueError(
                f"Technique '{technique}' is not "
                "deployable"
            )

        preset = {
            "id": (
                f"{method['id']}-"
                f"{architecture}-"
                f"{build_type}"
            ),
            "method": method["id"],
            "architecture": architecture,
            "build_type": build_type,
            "parameters": {},
        }

        resolved_parameters, parameter_errors = (
            self.parameters.resolve(
                method=method,
                preset=preset,
                cli_items=cli_parameters or [],
            )
        )

        provider_result = None
        payload_path = None

        if method.get(
            "requires_payload",
            False
        ):
            if payload_source is None:
                raise ValueError(
                    "This technique requires a payload"
                )

            provider = get_provider(
                provider_id
            )

            provider_result = provider.resolve(
                payload_source,
                **(
                    provider_options
                    or {}
                )
            )

            payload_path = provider_result[
                "path"
            ]

            if payload_type is None:
                accepted = method.get(
                    "payload_contract",
                    {}
                ).get(
                    "types",
                    method.get(
                        "payload_types",
                        []
                    )
                )

                if len(accepted) == 1:
                    payload_type = accepted[0]
                else:
                    raise ValueError(
                        "Payload type must be specified"
                    )

        compatibility_errors = (
            self.compatibility.validate(
                method=method,
                preset=preset,
                payload_path=payload_path,
                payload_type=payload_type,
                payload_transform=transform,
                payload_provider=(
                    provider_id
                    if payload_path is not None
                    else None
                ),
                parameter_errors=parameter_errors,
            )
        )

        if compatibility_errors:
            raise ValueError(
                "; ".join(
                    compatibility_errors
                )
            )

        build_id, build_dir = (
            self.builds.create(
                method=method,
                preset=preset,
                parameters=resolved_parameters,
            )
        )

        try:
            payload_info = None

            if payload_path is not None:
                payload_info = (
                    self.payloads.prepare(
                        payload_path=payload_path,
                        build_dir=build_dir,
                        method=method,
                        payload_type=payload_type,
                        transform=transform,
                    )
                )

                self.builds.attach_payload(
                    build_dir=build_dir,
                    payload_info=payload_info,
                    payload_type=payload_type,
                    provider_info=provider_result[
                        "provenance"
                    ],
                )

            generated = self.generator.generate(
                method=method,
                preset=preset,
                build_id=build_id,
                build_dir=build_dir,
                payload_info=payload_info,
                payload_type=payload_type,
                parameters=resolved_parameters,
            )

            compile_result = self.compiler.compile(
                method=method,
                preset=preset,
                generated_files=generated,
                build_dir=build_dir,
            )

            manifest = self.builds.mark_success(
                build_dir=build_dir,
                generated_files=generated,
                compile_result=compile_result,
            )

            return {
                "build_id": build_id,
                "build_dir": build_dir,
                "manifest": manifest,
            }

        except Exception as exc:
            self.builds.mark_failed(
                build_dir=build_dir,
                error=exc,
            )

            raise
