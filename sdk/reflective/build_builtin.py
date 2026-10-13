#!/usr/bin/env python3

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(ROOT)
)

from core.reflective_builtin import (
    ReflectiveBuiltinBuilder,
)


def main():
    builder = ReflectiveBuiltinBuilder(
        ROOT
    )

    try:
        output = builder.build(
            force=True
        )

    except Exception as exc:
        print(
            f"[!] {exc}"
        )
        return 1

    print(
        "[+] Mifa reflective DLL built"
    )

    print(
        f"[+] Output: {output}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
