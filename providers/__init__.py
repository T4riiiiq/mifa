from providers.external import ExternalProvider
from providers.file import FileProvider


PROVIDERS = {
    "file": FileProvider,
    "external": ExternalProvider,
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
