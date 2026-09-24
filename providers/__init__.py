from providers.file import FileProvider


PROVIDERS = {
    "file": FileProvider,
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
