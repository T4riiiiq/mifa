from pathlib import Path
import json


class MethodCatalog:
    def __init__(self, methods_dir: Path):
        self.methods_dir = methods_dir

    def discover(self):
        methods = []

        if not self.methods_dir.exists():
            return methods

        for path in sorted(self.methods_dir.iterdir()):
            if not path.is_dir():
                continue

            manifest = path / "method.json"

            if not manifest.exists():
                continue

            try:
                with manifest.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                data["_path"] = str(path)
                methods.append(data)

            except (json.JSONDecodeError, OSError) as exc:
                print(f"[!] Failed to read {manifest}: {exc}")

        return methods

    def get(self, method_id: str):
        for method in self.discover():
            if method.get("id") == method_id:
                return method

        return None
