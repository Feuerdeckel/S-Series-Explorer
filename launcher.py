from __future__ import annotations

# Version: 1.1.0

import sys
from pathlib import Path

# Allow the application to run directly from an extracted repository without
# installing packages or downloading build dependencies.
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from s_series_explorer.app import main


if __name__ == "__main__":
    main()
