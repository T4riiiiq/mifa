from pathlib import Path

from core.catalog import MethodCatalog


class TechniqueRegistry:
    def __init__(
        self,
        techniques_dir: Path
    ):
        self.catalog = MethodCatalog(
            techniques_dir
        )

    def discover(self):
        techniques = []

        for method in self.catalog.discover():
            operational = method.get(
                "operational"
            )

            if not isinstance(
                operational,
                dict
            ):
                continue

            if not operational.get(
                "deployable",
                False
            ):
                continue

            techniques.append(
                method
            )

        return techniques

    def get(
        self,
        identifier
    ):
        for method in self.discover():
            operational = method.get(
                "operational",
                {}
            )

            if (
                method.get("id") == identifier
                or operational.get("alias") == identifier
            ):
                return method

        return None
