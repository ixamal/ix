"""Pull Traktor remix-ready stem components from ``.stem.m4a`` on disk.

Uses [ixamal/stems](https://github.com/ixamal/stems) ``py.exec.extract_stems``
with ``--inplace --dot`` so each container gains ``Title.drums.m4a`` etc.
Vocals stream is skipped when a Mel `` - vocals.m4a`` already exists.
CRATER and ``stemit --sync-playlists`` run this before playlist rebuild.
"""

from __future__ import annotations

import os
import os
import subprocess
import sys
from pathlib import Path

from ix_crate.paths import STEMS_AUDIO
from ix_crate.stems_path import STEMS_REPO, ensure_stems_path


def stems_python() -> Path:
    ensure_stems_path()
    venv = STEMS_REPO / ".venv" / "bin" / "python3"
    return venv if venv.is_file() else Path(sys.executable)


def run_extract_tracks(*, execute: bool, root: Path | None = None) -> int:
    """Walk ``stems_audio`` and extract missing dot-role files from containers."""
    base = (root or STEMS_AUDIO).expanduser()
    if not base.is_dir():
        print("stems_audio missing; extract-tracks skipped.", flush=True)
        return 0
    py = stems_python()
    cmd = [
        str(py),
        "-u",
        "-m",
        "py.exec.extract_stems",
        "--path",
        str(base),
        "--inplace",
        "--dot",
    ]
    if execute:
        cmd.append("--execute")
    else:
        cmd.append("--dry-run")
    print(f"STEMIT extract-tracks: {' '.join(cmd)}", flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(STEMS_REPO)
    completed = subprocess.run(cmd, check=False, cwd=STEMS_REPO, env=env)
    return completed.returncode