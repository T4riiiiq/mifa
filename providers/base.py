from abc import ABC, abstractmethod
from pathlib import Path


class PayloadProvider(ABC):
    provider_id = None

    @abstractmethod
    def resolve(
        self,
        source
    ):
        raise NotImplementedError

    def _normalize_path(
        self,
        source
    ):
        return (
            Path(source)
            .expanduser()
            .resolve()
        )
