# Version: 1.1.0
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from tkinter import messagebox

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from s_series_explorer.app import main
except Exception:
    error_text = traceback.format_exc()
    (PROJECT_ROOT / "startup.log").write_text(error_text, encoding="utf-8")
    messagebox.showerror(
        "S-Series Explorer",
        "S-Series Explorer konnte nicht gestartet werden. Details stehen in startup.log.",
    )
    raise

if __name__ == "__main__":
    try:
        main()
    except Exception:
        error_text = traceback.format_exc()
        (PROJECT_ROOT / "startup.log").write_text(error_text, encoding="utf-8")
        messagebox.showerror(
            "S-Series Explorer",
            "S-Series Explorer wurde unerwartet beendet. Details stehen in startup.log.",
        )
        raise
