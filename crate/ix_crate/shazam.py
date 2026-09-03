"""Shazam file recognition via an off-repo Python 3.12 venv.

Homebrew Python 3.14 segfaults in shazamio-core. Recognition runs in
``~/local_tools/crate/shazam-venv`` (or ``SHAZAM_PYTHON`` / ``songrec``).
Never moves files. Never Discogs. Cache off-repo.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from ix_crate.identify import clean_text

SHAZAM_GAP = 1.6
SHAZAM_TIMEOUT = 90
SONGREC_TIMEOUT = 90
VENV_PYTHON = Path.home() / "local_tools" / "crate" / "shazam-venv" / "bin" / "python"
WORKER = r"""
import asyncio, json, sys, warnings
warnings.filterwarnings("ignore")
from shazamio import Shazam
path = sys.argv[1]
payload = asyncio.run(Shazam().recognize_song(path))
json.dump(payload, sys.stdout)
"""


def parse_shazam(payload: dict) -> dict | None:
    track = payload.get("track") or {}
    title = clean_text(str(track.get("title") or ""))
    artist = clean_text(str(track.get("subtitle") or ""))
    if not artist or not title:
        return None
    album = ""
    for section in track.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for meta in section.get("metadata") or []:
            if not isinstance(meta, dict):
                continue
            if str(meta.get("title") or "").strip().lower() == "album":
                album = clean_text(str(meta.get("text") or ""))
                if album:
                    break
        if album:
            break
    genre = ""
    genres = track.get("genres") or {}
    if isinstance(genres, dict):
        genre = clean_text(str(genres.get("primary") or ""))
    return {
        "artist": artist,
        "album": album,
        "title": title,
        "genre": genre,
        "source": "shazam",
    }


def _songrec_bin() -> str | None:
    found = shutil.which("songrec")
    if found:
        return found
    brew = Path("/opt/homebrew/bin/songrec")
    if brew.is_file():
        return str(brew)
    return None


def _shazam_python() -> str | None:
    env = os.environ.get("SHAZAM_PYTHON", "").strip()
    if env and Path(env).is_file():
        return env
    if VENV_PYTHON.is_file():
        return str(VENV_PYTHON)
    return None


def _recognize_songrec(path: Path) -> dict | None:
    binary = _songrec_bin()
    if not binary:
        return None
    try:
        raw = subprocess.check_output(
            [binary, "audio-file-to-recognized-song", str(path)],
            timeout=SONGREC_TIMEOUT,
            stderr=subprocess.DEVNULL,
        )
        payload = json.loads(raw.decode("utf-8"))
    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        TimeoutError,
        UnicodeDecodeError,
    ):
        return None
    if not isinstance(payload, dict):
        return None
    return parse_shazam(payload)


def _recognize_shazamio(path: Path) -> dict | None:
    python = _shazam_python()
    if not python:
        return None
    try:
        raw = subprocess.check_output(
            [python, "-c", WORKER, str(path)],
            timeout=SHAZAM_TIMEOUT,
            stderr=subprocess.DEVNULL,
        )
        payload = json.loads(raw.decode("utf-8"))
    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        TimeoutError,
        UnicodeDecodeError,
    ):
        return None
    if not isinstance(payload, dict):
        return None
    return parse_shazam(payload)


def shazam_identify(path: Path, cache: dict) -> dict | None:
    from ix_crate.lookup import _save_cache

    if not path.is_file():
        return None
    key = f"shazam::{str(path.resolve()).lower()}::{int(path.stat().st_mtime)}"
    if key in cache:
        return cache[key]
    time.sleep(SHAZAM_GAP)
    hit = _recognize_shazamio(path) or _recognize_songrec(path)
    cache[key] = hit
    _save_cache(cache)
    return hit
