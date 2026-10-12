from providers.external import ExternalProvider
from providers.file import FileProvider
from providers.msfvenom import MsfvenomProvider


PROVIDERS = {
    "file": FileProvider,
    "external": ExternalProvider,
    "msfvenom": MsfvenomProvider,
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
