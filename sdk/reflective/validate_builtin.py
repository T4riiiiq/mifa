#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(ROOT)
)

from core.pe import inspect_pe


DLL = (
    ROOT
    / "sdk"
    / "reflective"
    / "builtin"
    / "reference.dll"
)


def main():
    if not DLL.is_file():
        print(
            "[!] Built-in DLL does not exist"
        )
        return 1

    info = inspect_pe(
        DLL
    )

    if not info["is_dll"]:
        print(
            "[!] Artifact is not a DLL"
        )
        return 1

    exports = set(
        info.get(
            "exports",
            []
        )
    )

    if "ReflectiveLoader" not in exports:
        print(
            "[!] Missing ReflectiveLoader export"
        )
        return 1

    print(
        "[+] PE          : PASS"
    )

    print(
        "[+] DLL         : PASS"
    )

    print(
        "[+] Export      : ReflectiveLoader"
    )

    print(
        "[+] Build check : PASS"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
