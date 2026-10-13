import json
from pathlib import Path


class ReflectiveContract:
    ABI_VERSION = 1
    REQUIRED_EXPORT = "ReflectiveLoader"

    def __init__(self, root):
        self.root = Path(root)

    @property
    def manifest_path(self):
        return (
            self.root
            / "sdk"
            / "reflective"
            / "manifest.json"
        )

    def load(self):
        data = json.loads(
            self.manifest_path.read_text(
                encoding="utf-8"
            )
        )

        self.validate(data)
        return data

    def validate(self, data):
        if data.get(
            "abi_version"
        ) != self.ABI_VERSION:
            raise ValueError(
                "Unsupported Mifa Reflective ABI"
            )

        exports = data.get(
            "required_exports",
            []
        )

        if (
            self.REQUIRED_EXPORT
            not in exports
        ):
            raise ValueError(
                "ReflectiveLoader export "
                "is required"
            )

        modes = data.get(
            "modes"
        )

        if not isinstance(
            modes,
            dict
        ):
            raise ValueError(
                "Reflective modes are missing"
            )

        for mode in (
            "existing",
            "builtin",
        ):
            if mode not in modes:
                raise ValueError(
                    f"Missing reflective mode: "
                    f"{mode}"
                )

        return True

    def builtin_mode(self):
        return self.load()[
            "modes"
        ][
            "builtin"
        ]

    def builtin_status(self):
        return self.builtin_mode().get(
            "status",
            "planned"
        )

    def builtin_artifact(self):
        relative = (
            self.builtin_mode().get(
                "artifact",
                (
                    "sdk/reflective/"
                    "builtin/reference.dll"
                ),
            )
        )

        return (
            self.root
            / relative
        ).resolve()

    def builtin_available(self):
        return (
            self.builtin_status()
            in {
                "build-tested",
                "runtime-tested",
            }
        )

    def builtin_ready(self):
        return (
            self.builtin_status()
            == "runtime-tested"
        )
