"""Promote ``EDM, X`` genres to ``X``.

The 2026-08-30 pass cleared these from 11,031 files and 11,731 library rows.
Consolidating the migration drive brought the spelling back on tracks that
had never been through that pass.

Music.app does not re-read file tags, so genre has to be written twice: on
the file, and on the library row. Writing only the file leaves the column
browser unchanged, which is what made the first attempt look like a no-op.

``.m4p`` is never written. Those are DRM purchases and mutagen cannot
rewrite them; the library row is still corrected.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .music_dupes import _run_osascript, count_file_tracks
from .music_repair import RIFF_NO_ID3, _quote_as
from .paths import REPORTS

PREFIX = "EDM,"
BATCH = 200


class GenreError(RuntimeError):
    pass


@dataclass
class GenreRow:
    index: int
    persistent_id: str
    name: str
    genre: str
    path: str

    @property
    def promoted(self) -> str:
        return promote(self.genre)


@dataclass
class GenrePlan:
    rows: list[GenreRow] = field(default_factory=list)
    scanned: int = 0
    by_change: dict[str, int] = field(default_factory=dict)


def promote(genre: str) -> str:
    """``EDM, House`` -> ``House``. Anything else is returned unchanged.

    Only the leading ``EDM,`` is removed; ``EDM, House, Deep`` keeps
    ``House, Deep`` because the tail is the store's own subgenre spelling and
    is not ours to reinterpret.
    """
    text = (genre or "").strip()
    if not text.upper().startswith(PREFIX):
        return text
    return text[len(PREFIX) :].strip()


def scan(on_progress=None) -> GenrePlan:
    total = count_file_tracks()
    plan = GenrePlan(scanned=total)
    start = 1
    while start <= total:
        end = min(start + BATCH * 2 - 1, total)
        script = f"""
tell application "Music"
  set pids to (persistent ID of file tracks {start} thru {end} of library playlist 1) as list
  set nms to (name of file tracks {start} thru {end} of library playlist 1) as list
  set gns to (genre of file tracks {start} thru {end} of library playlist 1) as list
  set locs to (location of file tracks {start} thru {end} of library playlist 1) as list
  set out to ""
  repeat with i from 1 to count of pids
    set h to ""
    try
      set h to POSIX path of (item i of locs)
    end try
    set out to out & (item i of pids as text) & tab & (item i of gns as text) & tab & (item i of nms as text) & tab & h & linefeed
  end repeat
  return out
end tell
"""
        offset = start
        for line in _run_osascript(script, timeout=300).splitlines():
            if not line.strip():
                offset += 1
                continue
            parts = (line.split("\t") + [""] * 4)[:4]
            pid, genre, name, path = (p.strip() for p in parts)
            if pid and genre.upper().startswith(PREFIX):
                plan.rows.append(
                    GenreRow(
                        index=offset,
                        persistent_id=pid,
                        name=name,
                        genre=genre,
                        path=path,
                    )
                )
                label = f"{genre} -> {promote(genre)}"
                plan.by_change[label] = plan.by_change.get(label, 0) + 1
            offset += 1
        if on_progress:
            on_progress(min(end, total), total)
        start = end + 1
    return plan


def write_file_genre(path: Path, genre: str) -> bool:
    """Write genre on the file. ``.m4p`` is DRM; WAV/AIFF must not get ID3."""
    suffix = path.suffix.lower()
    if suffix == ".m4p" or suffix in RIFF_NO_ID3 or not path.is_file():
        return False
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return False
    try:
        audio = MutagenFile(path, easy=True)
        if audio is None:
            return False
        audio["genre"] = genre
        audio.save()
    except Exception:
        return False
    return True


def apply_library(rows: list[GenreRow], *, on_progress=None) -> tuple[int, int]:
    """Set genre on library rows positionally, confirming the ID at each index."""
    done = skipped = 0
    for offset in range(0, len(rows), BATCH):
        chunk = rows[offset : offset + BATCH]
        entries = "".join(
            f'  set plan to plan & {{{{{r.index}, "{_quote_as(r.persistent_id)}", '
            f'"{_quote_as(r.promoted)}"}}}}\n'
            for r in chunk
        )
        script = f"""
tell application "Music"
  set plan to {{}}
{entries}
  set okCount to 0
  set skipCount to 0
  repeat with e in plan
    set t to file track (item 1 of e) of library playlist 1
    if (persistent ID of t as text) is (item 2 of e) then
      try
        set genre of t to (item 3 of e)
        set okCount to okCount + 1
      on error
        set skipCount to skipCount + 1
      end try
    else
      set skipCount to skipCount + 1
    end if
  end repeat
  return (okCount as text) & tab & (skipCount as text)
end tell
"""
        result = _run_osascript(script, timeout=600).strip()
        parts = (result.split("\t") + ["0", "0"])[:2]
        done += int(parts[0] or 0)
        skipped += int(parts[1] or 0)
        if on_progress:
            on_progress(min(offset + len(chunk), len(rows)), len(rows))
    return done, skipped


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"music-genre-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate music-genre",
        description="Promote 'EDM, X' genres to 'X' on files and library rows.",
    )
    parser.add_argument("--execute", action="store_true", help="apply the changes")
    parser.add_argument(
        "--passes",
        type=int,
        default=3,
        help="rescan rounds; editing a row can reorder the library",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    total_lib = total_files = 0
    rounds = max(args.passes, 1) if args.execute else 1
    for round_no in range(1, rounds + 1):
        plan = scan(on_progress=lambda d, t: print(f"scan {d}/{t}", flush=True))
        print(f"EDM rows {len(plan.rows)} of {plan.scanned}", flush=True)
        for label, count in sorted(plan.by_change.items(), key=lambda kv: -kv[1]):
            print(f"  {count:5}  {label}", flush=True)

        if not plan.rows:
            if not args.execute:
                report = write_report(
                    {
                        "scanned": plan.scanned,
                        "rows": 0,
                        "by_change": {},
                        "executed": False,
                    }
                )
                print(f"report {report}", flush=True)
                print("dry run, nothing changed. re-run with --execute", flush=True)
                return 0
            break
        if not args.execute:
            report = write_report(
                {
                    "scanned": plan.scanned,
                    "rows": len(plan.rows),
                    "by_change": plan.by_change,
                    "executed": False,
                }
            )
            print(f"report {report}", flush=True)
            print("dry run, nothing changed. re-run with --execute", flush=True)
            return 0

        wrote = 0
        for row in plan.rows:
            if row.path and write_file_genre(Path(row.path), row.promoted):
                wrote += 1
        total_files += wrote
        print(f"pass {round_no}: file tags written {wrote}", flush=True)

        done, skipped = apply_library(
            plan.rows,
            on_progress=lambda d, t: print(f"library {d}/{t}", flush=True),
        )
        total_lib += done
        print(f"pass {round_no}: library rows set {done}  skipped {skipped}", flush=True)
        if not done:
            break

    if args.execute:
        report = write_report(
            {
                "library_rows": total_lib,
                "file_tags": total_files,
                "executed": True,
            }
        )
        print(f"report {report}", flush=True)
    print(f"library rows {total_lib}  file tags {total_files}", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
