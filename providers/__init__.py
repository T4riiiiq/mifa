from providers.external import ExternalProvider
from providers.file import FileProvider
from providers.msfvenom import MsfvenomProvider
from providers.reflective_builtin import ReflectiveBuiltinProvider


PROVIDERS = {
    "file": FileProvider,
    "external": ExternalProvider,
    "msfvenom": MsfvenomProvider,
    "reflective-builtin": ReflectiveBuiltinProvider,
}


def get_provider(
    provider_id
):
    provider_class = PROVIDERS.get(
        provider_id
    )

    if provider_class is None:
        raise ValueError(
            f"Unknown payload provider: "
            f"{provider_id}"
        )

    return provider_class()


def list_providers():
    return sorted(
        PROVIDERS
    )
