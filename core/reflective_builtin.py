import shutil
import subprocess
from pathlib import Path


class ReflectiveBuiltinBuilder:
    def __init__(self, root):
        self.root = Path(root)

        self.base = (
            self.root
            / "sdk"
            / "reflective"
            / "builtin"
        )

        self.vendor = (
            self.base
            / "vendor"
            / "stephenfewer"
        )

        self.loader_source = (
            self.vendor
            / "ReflectiveLoader.c"
        )

        self.dll_source = (
            self.base
            / "src"
            / "reference_dll.c"
        )

        self.output = (
            self.base
            / "reference.dll"
        )

    def inputs(self):
        return [
            self.loader_source,
            self.vendor / "ReflectiveLoader.h",
            self.vendor / "ReflectiveDLLInjection.h",
            self.dll_source,
        ]

    def validate_sources(self):
        missing = [
            path
            for path in self.inputs()
            if not path.is_file()
        ]

        if missing:
            raise FileNotFoundError(
                "Missing built-in reflective source(s): "
                + ", ".join(
                    str(path)
                    for path in missing
                )
            )

    def needs_build(self):
        if not self.output.is_file():
            return True

        output_mtime = (
            self.output.stat().st_mtime
        )

        return any(
            path.stat().st_mtime
            > output_mtime
            for path in self.inputs()
        )

    def build(self, force=False):
        self.validate_sources()

        if (
            not force
            and not self.needs_build()
        ):
            return self.output

        compiler = shutil.which(
            "x86_64-w64-mingw32-gcc"
        )

        if compiler is None:
            raise RuntimeError(
                "x86_64-w64-mingw32-gcc "
                "is required to build the "
                "Mifa reflective DLL"
            )

        self.output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        command = [
            compiler,
            "-shared",
            "-O2",
            "-Wall",
            "-Wextra",
            "-DWIN_X64",
            "-DREFLECTIVEDLLINJECTION_VIA_LOADREMOTELIBRARYR",
            "-DREFLECTIVEDLLINJECTION_CUSTOM_DLLMAIN",
            f"-I{self.vendor}",
            str(self.loader_source),
            str(self.dll_source),
            "-o",
            str(self.output),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "unknown compiler error"
            )

            raise RuntimeError(
                "Built-in reflective DLL "
                f"build failed:\n{message}"
            )

        return self.output
