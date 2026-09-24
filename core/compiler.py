import shutil
import subprocess


class Compiler:
    COMPILERS = {
        ("c", "x64"):
            "x86_64-w64-mingw32-gcc",

        ("c", "x86"):
            "i686-w64-mingw32-gcc",

        ("cpp", "x64"):
            "x86_64-w64-mingw32-g++",

        ("cpp", "x86"):
            "i686-w64-mingw32-g++"
    }

    def compile(
        self,
        method,
        preset,
        generated_files,
        build_dir
    ):
        language = method.get(
            "language"
        )

        architecture = preset.get(
            "architecture"
        )

        build_type = preset.get(
            "build_type",
            "release"
        )

        compiler_name = self.COMPILERS.get(
            (
                language,
                architecture
            )
        )

        if compiler_name is None:
            raise ValueError(
                f"No compiler configured for "
                f"{language}/{architecture}"
            )

        compiler_path = shutil.which(
            compiler_name
        )

        if compiler_path is None:
            raise RuntimeError(
                f"Compiler not found: "
                f"{compiler_name}"
            )

        compile_sources = [
            item["path"]
            for item in generated_files
            if item["compile"]
        ]

        if not compile_sources:
            raise RuntimeError(
                "No compilable source files "
                "were generated"
            )

        output_dir = (
            build_dir / "output"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            output_dir
            / method.get(
                "output_name",
                "output.exe"
            )
        )

        command = [
            compiler_path
        ]

        command.extend(
            str(path)
            for path in compile_sources
        )

        command.extend([
            "-o",
            str(output_path)
        ])

        if language == "cpp":
            command.extend([
                "-std=c++17",
                "-static-libgcc",
                "-static-libstdc++"
            ])

        if build_type == "release":
            command.append(
                "-O2"
            )

        elif build_type == "debug":
            command.extend([
                "-O0",
                "-g"
            ])

        else:
            raise ValueError(
                f"Unsupported build type: "
                f"{build_type}"
            )

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "Compilation failed"
            )

        if not output_path.exists():
            raise RuntimeError(
                "Compiler exited successfully "
                "but output file was not created"
            )

        return {
            "compiler":
                compiler_name,

            "command":
                command,

            "output":
                output_path,

            "stdout":
                result.stdout.strip(),

            "stderr":
                result.stderr.strip()
        }
