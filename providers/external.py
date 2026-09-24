from providers.base import PayloadProvider


class ExternalProvider(PayloadProvider):
    provider_id = "external"

    def resolve(
        self,
        source,
        **options
    ):
        path = self._normalize_path(
            source
        )

        if not path.exists():
            raise FileNotFoundError(
                f"External payload not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"External payload source is not "
                f"a file: {path}"
            )

        producer = str(
            options.get(
                "producer",
                "external"
            )
        ).strip()

        if not producer:
            producer = "external"

        return {
            "provider": self.provider_id,
            "path": path,
            "provenance": {
                "provider": self.provider_id,
                "producer": producer,
                "source_name": path.name,
                "source_path": str(path),
            },
        }
