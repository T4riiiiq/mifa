from providers.base import PayloadProvider


class FileProvider(PayloadProvider):
    provider_id = "file"

    def resolve(
        self,
        source
    ):
        path = self._normalize_path(
            source
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Payload file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Payload source is not a file: {path}"
            )

        return {
            "provider": self.provider_id,
            "path": path,
            "provenance": {
                "provider": self.provider_id,
                "source_name": path.name,
                "source_path": str(path),
            },
        }
