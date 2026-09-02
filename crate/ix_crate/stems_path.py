"""Put the off-repo stems factory on sys.path so crate can use py.utils.progress."""

from __future__ import annotations

import sys
from pathlib import Path

STEMS_REPO = Path.home() / "github" / "ixamal" / "stems"


def ensure_stems_path() -> Path:
    progress = STEMS_REPO / "py" / "utils" / "progress.py"
    if not progress.is_file():
        raise FileNotFoundError(
            f"stems factory missing ({progress}). Clone ixamal/stems next to ix."
        )
    root = str(STEMS_REPO)
    if root not in sys.path:
        sys.path.insert(0, root)
    return STEMS_REPO
