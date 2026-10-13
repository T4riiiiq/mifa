from pathlib import Path

from core.reflective import (
    ReflectiveContract,
)

from core.reflective_builtin import (
    ReflectiveBuiltinBuilder,
)

from providers.base import (
    PayloadProvider,
)


class ReflectiveBuiltinProvider(
    PayloadProvider
):
    provider_id = (
        "reflective-builtin"
    )

    def resolve(
        self,
        source=None,
        **options
    ):
        root = (
            Path(__file__)
            .resolve()
            .parents[1]
        )

        contract = (
            ReflectiveContract(
                root
            )
        )

        data = contract.load()
        status = (
            contract.builtin_status()
        )

        if not contract.builtin_available():
            raise ValueError(
                "Mifa built-in Reflective DLL "
                f"is not available "
                f"(status: {status})"
            )

        builder = (
            ReflectiveBuiltinBuilder(
                root
            )
        )

        artifact = builder.build()

        return {
            "provider":
                self.provider_id,

            "path":
                artifact,

            "provenance": {
                "provider":
                    self.provider_id,

                "producer":
                    "mifa-reflective",

                "loader_abi":
                    data[
                        "abi_version"
                    ],

                "validation":
                    status,

                "source_name":
                    artifact.name,

                "source_path":
                    str(
                        artifact
                    ),
            },
        }
