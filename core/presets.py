from pathlib import Path
import json


class PresetStore:
    def __init__(self, presets_dir: Path):
        self.presets_dir = presets_dir

    def discover(self):
        presets = []

        if not self.presets_dir.exists():
            return presets

        for path in sorted(self.presets_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                data["_path"] = str(path)
                presets.append(data)

            except (json.JSONDecodeError, OSError) as exc:
                print(f"[!] Failed to read {path}: {exc}")

        return presets

    def get(self, preset_id: str):
        for preset in self.discover():
            if preset.get("id") == preset_id:
                return preset

        return None
