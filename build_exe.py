"""Build helper for creating a one-file Windows executable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__version__ = "1.0.0"

APP_NAME = "S-Series-Explorer"
ENTRYPOINT = Path(__file__).with_name("s_series_explorer.py")


def main() -> int:
    if not ENTRYPOINT.exists():
        print(f"Missing entrypoint: {ENTRYPOINT}", file=sys.stderr)
        return 1
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        str(ENTRYPOINT),
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
