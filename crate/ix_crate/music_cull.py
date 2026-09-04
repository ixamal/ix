"""Remove Music.app rows whose file is gone or will not play.

Terrarum has been searched. What is still ``!`` is not coming back from
that drive. These rows are ghosts: they take a crate slot, they throw the
Locate dialog, and they have no audio on disk.

A row is dropped only when:

* Music.app has no location, or the path is not a file
* the file is a WAV/AIFF that no longer starts with RIFF/FORM (the ID3
  prepend), or is empty

``.m4p`` purchases are left alone even if ffmpeg cannot decode them.
Valid files are never unlinked. Dry-run is the default.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .music_dupes import MusicDupesError, _run_osascript, count_file_tracks, delete_library_row
from .paths import REPORTS
from .riff_repair import is_form, is_riff

BATCH = 400


class CullError(RuntimeError):
    pass


@dataclass
class CullRow:
    persistent_id: str
    artist: str
    name: str
    path: str
    reason: str


def verdict(path: str) -> str:
    """``missing``, ``corrupt``, or ``keep``."""
    text = (path or "").strip()
    if not text:
        return "missing"
    file = Path(text)
    if not file.is_file():
        return "missing"
    suffix = file.suffix.lower()
    if suffix == ".m4p":
        return "keep"
    try:
        size = file.stat().st_size
    except OSError:
        return "missing"
    if size < 64:
        return "corrupt"
    if suffix == ".wav" and not is_riff(file):
        return "corrupt"
    if suffix in {".aiff", ".aif"} and not is_form(file):
        return "corrupt"
    return "keep"


def scan(on_progress=None) -> tuple[list[CullRow], int]:
    total = count_file_tracks()
    drop: list[CullRow] = []
    start = 1
    while start <= total:
        end = min(start + BATCH - 1, total)
        script = f"""
tell application "Music"
  set pids to (persistent ID of file tracks {start} thru {end} of library playlist 1) as list
  set nms to (name of file tracks {start} thru {end} of library playlist 1) as list
  set ars to (artist of file tracks {start} thru {end} of library playlist 1) as list
  set locs to (location of file tracks {start} thru {end} of library playlist 1) as list
  set out to ""
  repeat with i from 1 to count of pids
    set h to ""
    try
      set h to POSIX path of (item i of locs)
    end try
    set out to out & (item i of pids as text) & tab & (item i of ars as text) & tab & (item i of nms as text) & tab & h & linefeed
  end repeat
  return out
end tell
"""
        for line in _run_osascript(script, timeout=300).splitlines():
            if not line.strip():
                continue
            pid, artist, name, path = (line.split("\t") + [""] * 4)[:4]
            pid = pid.strip()
            if not pid:
                continue
            reason = verdict(path.strip())
            if reason != "keep":
                drop.append(
                    CullRow(
                        persistent_id=pid,
                        artist=artist.strip(),
                        name=name.strip(),
                        path=path.strip(),
                        reason=reason,
                    )
                )
        if on_progress:
            on_progress(min(end, total), total)
        start = end + 1
    return drop, total


def drop_row(row: CullRow) -> None:
    """Delete the library row. A missing path has nothing to trash.

    If Music.app bins a *corrupt* file, that is the point. A valid file
    disappearing is a stop — we never classify those as drop.
    """
    file = Path(row.path) if row.path else None
    existed = bool(file and file.is_file() and row.reason == "keep")
    delete_library_row(row.persistent_id)
    if existed and file is not None and not file.is_file():
        raise CullError(f"Music.app removed a kept file. Stopped. {file}")


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"music-cull-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate music-cull",
        description="Drop Music.app rows with no file or unreadable audio.",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, scanned = scan(on_progress=lambda d, t: print(f"scan {d}/{t}", flush=True))
    missing = sum(1 for r in rows if r.reason == "missing")
    corrupt = sum(1 for r in rows if r.reason == "corrupt")
    print(
        f"scanned {scanned}  drop {len(rows)}  missing {missing}  corrupt {corrupt}",
        flush=True,
    )
    for row in rows[: args.limit]:
        print(f"  {row.reason:8}  {row.artist[:24]:26} {row.name[:42]}", flush=True)

    payload = {
        "scanned": scanned,
        "drop": len(rows),
        "missing": missing,
        "corrupt": corrupt,
        "executed": False,
        "rows": [
            {
                "persistent_id": r.persistent_id,
                "artist": r.artist,
                "name": r.name,
                "path": r.path,
                "reason": r.reason,
            }
            for r in rows
        ],
    }
    if not args.execute:
        report = write_report(payload)
        print(f"report {report}", flush=True)
        print("dry run, nothing deleted. re-run with --execute", flush=True)
        return 0

    done = 0
    for i, row in enumerate(rows, start=1):
        try:
            drop_row(row)
            done += 1
        except (CullError, MusicDupesError) as exc:
            print(f"stop: {exc}", flush=True)
            payload["executed"] = True
            payload["dropped"] = done
            write_report(payload)
            return 1
        if i % 25 == 0:
            print(f"drop {i}/{len(rows)}", flush=True)
    payload["executed"] = True
    payload["dropped"] = done
    report = write_report(payload)
    print(f"dropped {done}  report {report}", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
