"""Name Music.app files from the library row, then point Songs at the new path.

``music-fix`` writes artist / album / title into Music.app and onto owned
tags. It never moves ``Media.localized``. That is why a row can read
Moby / Play / Honey while the file is still ``Track 01.m4a``. DJ software
and ``ls`` see the disc name, not the library.

This command is the missing file-management step:

* folder = album artist (else artist) / album (or ``Singles``)
* file   = ``NN Title`` when Music.app has a track number, else ``Title``
* stay in the tree you already live in (artist-root crate **or**
  ``Media.localized/Music/`` copy-on-add). Never hoist between them.
* leave a real filename alone (Beatport ``Artist - Title`` stays)
* rename only when the disc name is a placeholder (``Track 01``) **and**
  Music.app already has a real title
* never invent a title; leftover ``Track 01`` rows stay ``Track 01``
* never overwrite, never touch ``.stem.m4a`` / ``.m4p``, never leave
  ``Media.localized``

Music.app **Keep Music Media folder organized** stays **Off**. That switch
would dump the artist-root crate into ``Music/`` and break the path-stable
Traktor / Rekordbox crate. This command organizes in place and writes a
remap report for [music_migration](https://github.com/ixamal/music_migration).

Dry-run is the default. ``--execute`` renames, then ``set location``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from ix_crate.consolidate import unique_dest
from ix_crate.families import is_audio
from ix_crate.identify import (
    is_placeholder_album_folder,
    is_placeholder_artist,
    is_placeholder_title,
    normalize_title,
    sanitize,
    strip_track_number,
)
from ix_crate.music_dupes import (
    MusicDupesError,
    _clean_field,
    _parse_int,
    _run_osascript,
    count_file_tracks,
    music_running,
)
from ix_crate.music_repair import _quote_as, set_track_location, strip_copy_suffix
from ix_crate.paths import APPLE_MEDIA_SKIP_DIRS, APPLE_MUSIC, REPORTS, STEM_SUFFIXES

BATCH = 200
SKIP_SUFFIX = STEM_SUFFIXES + (".m4p",)
JUNK_ALBUMS = {
    "rain or shine summer",
    "unknown album",
    "untitled",
    "untitled album",
}
MAX_NAME_BYTES = 255


class OrganizeError(RuntimeError):
    pass


@dataclass
class OrganizeRow:
    persistent_id: str
    artist: str
    album_artist: str
    album: str
    name: str
    track_number: int
    disc_number: int
    location: str


@dataclass
class OrganizeMove:
    persistent_id: str
    source: str
    dest: str
    artist: str
    album: str
    title: str
    reason: str


@dataclass
class OrganizePlan:
    moves: list[OrganizeMove] = field(default_factory=list)
    skipped: dict[str, int] = field(default_factory=dict)
    scanned: int = 0


def is_junk_album(value: str) -> bool:
    return is_placeholder_album_folder(value) or normalize_title(value) in JUNK_ALBUMS


def filename_is_junk(stem: str) -> bool:
    """``Track 01``, ``01 Track 01``, ``Track 1 (2)`` — not a real title."""
    raw = (stem or "").strip()
    if not raw:
        return True
    if is_placeholder_title(raw):
        return True
    return is_placeholder_title(strip_copy_suffix(strip_track_number(raw)))


def filing_artist(row: OrganizeRow) -> str:
    """Album artist wins so mix CDs stay under the DJ. VA is not a home."""
    for value in (row.album_artist, row.artist):
        if value and not is_placeholder_artist(value):
            return value
    return ""


def filing_album(row: OrganizeRow) -> str:
    if row.album.strip() and not is_junk_album(row.album):
        return row.album.strip()
    return "Singles"


def filing_title(row: OrganizeRow) -> str:
    title = strip_track_number(row.name or "").strip()
    if title and not is_placeholder_title(title):
        return title
    return ""


def tree_root(path: Path, media_root: Path) -> Path | None:
    """Artist-root crate or ``Music/`` copy-on-add. Never hoist."""
    try:
        rel = path.expanduser().resolve().relative_to(media_root.expanduser().resolve())
    except ValueError:
        return None
    parts = list(rel.parts)
    if parts and parts[0] == "Music":
        return media_root / "Music"
    return media_root


def current_artist_album(path: Path, root: Path) -> tuple[str, str]:
    try:
        rel = path.expanduser().resolve().parent.relative_to(root.expanduser().resolve())
    except ValueError:
        return "", ""
    parts = [part for part in rel.parts if part not in APPLE_MEDIA_SKIP_DIRS]
    artist = parts[0] if parts else ""
    album = parts[1] if len(parts) >= 2 else ""
    return artist, album


def folder_matches(path: Path, artist: str, album: str, root: Path) -> bool:
    have_artist, have_album = current_artist_album(path, root)
    return normalize_title(have_artist) == normalize_title(artist) and normalize_title(
        have_album
    ) == normalize_title(album)


def organized_filename(
    title: str, suffix: str, *, track_number: int = 0, disc_number: int = 0
) -> str:
    name = sanitize(title, "")
    if not name:
        return ""
    if disc_number > 1 and track_number > 0:
        prefix = f"{disc_number}-{track_number:02d} "
    elif track_number > 0:
        prefix = f"{track_number:02d} "
    else:
        prefix = ""
    return _fit_filename(prefix + name, suffix)


def _fit_filename(stem: str, suffix: str) -> str:
    suffix = suffix or ""
    budget = MAX_NAME_BYTES - len(suffix.encode("utf-8"))
    encoded = stem.encode("utf-8")
    while stem and len(encoded) > budget:
        stem = stem[:-1]
        encoded = stem.encode("utf-8")
    return stem.rstrip(" .") + suffix


def paths_equal(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.normpath(str(left))) == os.path.normcase(
        os.path.normpath(str(right))
    )


def skip_reason(row: OrganizeRow, *, media_root: Path) -> str:
    loc = (row.location or "").strip()
    if not loc:
        return "no_file"
    path = Path(loc)
    low = path.name.lower()
    if any(low.endswith(suffix) for suffix in SKIP_SUFFIX) or low.endswith(".itlp"):
        return "skip_stem_or_drm"
    if path.suffix.lower() == ".itlp" or loc.endswith(".itlp/"):
        return "skip_stem_or_drm"
    if not path.is_file() or not is_audio(path):
        return "no_file"
    if tree_root(path, media_root) is None:
        return "outside_media"
    if not filing_artist(row):
        return "placeholder_identity"
    if not filing_title(row) and filename_is_junk(path.stem):
        return "placeholder_identity"
    return ""


def planned_dest(row: OrganizeRow, *, media_root: Path) -> Path | None:
    skip = skip_reason(row, media_root=media_root)
    if skip:
        return None
    path = Path(row.location)
    root = tree_root(path, media_root)
    if root is None:
        return None
    artist = sanitize(filing_artist(row), "")
    album = sanitize(filing_album(row), "Singles")
    if not artist:
        return None
    title = filing_title(row)
    if filename_is_junk(path.stem):
        if not title:
            return None
        name = organized_filename(
            title,
            path.suffix,
            track_number=row.track_number,
            disc_number=row.disc_number,
        )
    else:
        name = path.name
    if not name:
        return None
    return root / artist / album / name


def move_reason(row: OrganizeRow, dest: Path, *, media_root: Path) -> str:
    path = Path(row.location)
    root = tree_root(path, media_root)
    assert root is not None
    junk = filename_is_junk(path.stem)
    wrong = not folder_matches(path, filing_artist(row), filing_album(row), root)
    if junk and wrong:
        return "placeholder_and_folder"
    if junk:
        return "placeholder_name"
    if wrong:
        return "wrong_folder"
    return ""


def plan_row(
    row: OrganizeRow,
    *,
    media_root: Path,
    taken: set[Path],
) -> OrganizeMove | str:
    """A move, or a skip reason."""
    reason = skip_reason(row, media_root=media_root)
    if reason:
        return reason
    dest = planned_dest(row, media_root=media_root)
    if dest is None:
        return "placeholder_identity"
    source = Path(row.location).expanduser()
    if paths_equal(source, dest):
        return "already_organized"
    why = move_reason(row, dest, media_root=media_root)
    if not why:
        return "already_organized"
    dest = unique_dest(dest, taken)
    taken.add(dest)
    return OrganizeMove(
        persistent_id=row.persistent_id,
        source=str(source),
        dest=str(dest),
        artist=filing_artist(row),
        album=filing_album(row),
        title=filing_title(row) or Path(dest).stem,
        reason=why,
    )


def plan_rows(rows: list[OrganizeRow], *, media_root: Path) -> OrganizePlan:
    plan = OrganizePlan(scanned=len(rows))
    taken: set[Path] = set()
    claimed: set[str] = set()
    for row in rows:
        loc = os.path.normcase(os.path.normpath(row.location or ""))
        if loc and loc in claimed:
            plan.skipped["shared_file"] = plan.skipped.get("shared_file", 0) + 1
            continue
        result = plan_row(row, media_root=media_root, taken=taken)
        if isinstance(result, OrganizeMove):
            plan.moves.append(result)
            if loc:
                claimed.add(loc)
            continue
        plan.skipped[result] = plan.skipped.get(result, 0) + 1
    return plan


def _clean_missing(value: str) -> str:
    text = _clean_field(value)
    return "" if text.lower() == "missing value" else text


def _dump_script(track_ref: str) -> str:
    """Bulk read. Per-item try: album artist / track / disc are often missing."""
    return f'''
tell application "Music"
  set pids to persistent ID of {track_ref}
  set ars to artist of {track_ref}
  set aas to album artist of {track_ref}
  set als to album of {track_ref}
  set nms to name of {track_ref}
  set trs to track number of {track_ref}
  set dcs to disc number of {track_ref}
  set locs to location of {track_ref}
  set out to ""
  repeat with i from 1 to count of pids
    set locText to ""
    try
      set locText to POSIX path of (item i of locs)
    end try
    set aaText to ""
    try
      set aaText to item i of aas as text
      if aaText is "missing value" then set aaText to ""
    end try
    set trText to "0"
    try
      set trText to item i of trs as text
      if trText is "missing value" then set trText to "0"
    end try
    set dcText to "0"
    try
      set dcText to item i of dcs as text
      if dcText is "missing value" then set dcText to "0"
    end try
    set out to out & (item i of pids as text) & tab & (item i of ars as text) & tab & aaText & tab & (item i of als as text) & tab & (item i of nms as text) & tab & trText & tab & dcText & tab & locText & linefeed
  end repeat
  return out
end tell
'''


def dump_organize_batch(start: int, end: int) -> list[OrganizeRow]:
    ref = f"file tracks {start} thru {end} of library playlist 1"
    return _parse_dump(_run_osascript(_dump_script(ref), timeout=180))


def dump_organize_playlist(name: str) -> list[OrganizeRow]:
    quoted = _quote_as(name)
    script = f'''
tell application "Music"
  try
    set p to user playlist "{quoted}"
  on error
    error "playlist not found: {quoted}"
  end try
end tell
''' + _dump_script("file tracks of user playlist \"" + quoted + "\"")
    return _parse_dump(_run_osascript(script, timeout=180))


def _parse_dump(text: str) -> list[OrganizeRow]:
    rows: list[OrganizeRow] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 8:
            parts = parts + [""] * (8 - len(parts))
        pid, artist, album_artist, album, name, track, disc, location = parts[:8]
        if not pid.strip():
            continue
        rows.append(
            OrganizeRow(
                persistent_id=pid.strip(),
                artist=_clean_missing(artist),
                album_artist=_clean_missing(album_artist),
                album=_clean_missing(album),
                name=_clean_missing(name),
                track_number=_parse_int(track),
                disc_number=_parse_int(disc),
                location=location.strip(),
            )
        )
    return rows


def scan_library(*, media_root: Path, on_progress=None) -> list[OrganizeRow]:
    if not music_running():
        raise MusicDupesError("Music.app is not running. Open it and retry.")
    total = count_file_tracks()
    rows: list[OrganizeRow] = []
    start = 1
    while start <= total:
        end = min(start + BATCH - 1, total)
        if on_progress:
            on_progress(end, total)
        rows.extend(dump_organize_batch(start, end))
        start = end + 1
    return rows


def assert_under_media(path: Path, media_root: Path) -> Path:
    resolved = Path(os.path.normpath(str(path.expanduser())))
    base = Path(os.path.normpath(str(media_root.expanduser())))
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise OrganizeError(f"refusing path outside Media.localized: {path}") from exc
    return resolved


def prune_empty(start: Path, stop: Path) -> list[str]:
    """Remove empty album/artist folders left behind. Never the media root."""
    removed: list[str] = []
    current = start.expanduser()
    stop_res = stop.expanduser().resolve()
    while True:
        try:
            current.resolve().relative_to(stop_res)
        except ValueError:
            break
        if current.resolve() == stop_res:
            break
        try:
            next(current.iterdir())
            break
        except StopIteration:
            parent = current.parent
            try:
                current.rmdir()
            except OSError:
                break
            removed.append(str(current))
            current = parent
        except OSError:
            break
    return removed


def apply_move(
    move: OrganizeMove,
    *,
    media_root: Path,
    set_location: Callable[[str, Path], None] | None = None,
) -> dict[str, Any]:
    """Rename on the same volume, then point Music.app at the new path."""
    source = assert_under_media(Path(move.source), media_root)
    dest = assert_under_media(Path(move.dest), media_root)
    if not source.is_file():
        raise OrganizeError(f"missing source {source}")
    if not paths_equal(source, dest) and dest.exists():
        raise OrganizeError(f"refusing to overwrite {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    source.rename(dest)
    linker = set_location if set_location is not None else set_track_location
    try:
        linker(move.persistent_id, dest)
    except Exception as exc:
        return {
            "ok": False,
            "moved": True,
            "relinked": False,
            "error": str(exc),
            "pruned": [],
        }
    pruned = prune_empty(source.parent, tree_root(dest, media_root) or media_root)
    return {"ok": True, "moved": True, "relinked": True, "error": "", "pruned": pruned}


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"music-organize-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate music-organize",
        description=(
            "Rename Media.localized files from Music.app metadata and "
            "relink Songs. Track 01 stays Track 01 when the library has "
            "no real title. Dry-run default."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="rename files and set Music.app location. Default is dry-run.",
    )
    parser.add_argument(
        "--playlist",
        default="",
        help="limit to one Music.app playlist (try Fix first)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="cap planned moves (0 = no cap)",
    )
    parser.add_argument(
        "--media-root",
        type=Path,
        default=None,
        help="override Media.localized (tests / a copy). Must stay under ~/Music.",
    )
    return parser


def run(
    *,
    execute: bool,
    playlist: str = "",
    limit: int = 0,
    media_root: Path | None = None,
    rows: list[OrganizeRow] | None = None,
    set_location: Callable[[str, Path], None] | None = None,
) -> dict[str, Any]:
    root = (media_root or APPLE_MUSIC).expanduser()
    if rows is None:
        if playlist:
            if not music_running():
                raise MusicDupesError("Music.app is not running. Open it and retry.")
            rows = dump_organize_playlist(playlist)
        else:
            rows = scan_library(
                media_root=root,
                on_progress=lambda done, total: print(f"scan {done}/{total}", flush=True),
            )
    plan = plan_rows(rows, media_root=root)
    moves = plan.moves[:limit] if limit else plan.moves
    payload: dict[str, Any] = {
        "scanned": plan.scanned,
        "moves": [asdict(item) for item in moves],
        "skipped": plan.skipped,
        "executed": False,
        "applied": 0,
        "relink_failed": 0,
        "remaps": [{"from": item.source, "to": item.dest} for item in moves],
    }
    print(
        f"scanned {plan.scanned}  moves {len(moves)}  skipped {sum(plan.skipped.values())}",
        flush=True,
    )
    for label, count in sorted(plan.skipped.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  skip {count:5}  {label}", flush=True)
    by_reason: dict[str, int] = {}
    for item in moves:
        by_reason[item.reason] = by_reason.get(item.reason, 0) + 1
    for label, count in sorted(by_reason.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  move {count:5}  {label}", flush=True)
    if not execute:
        payload["report"] = str(write_report(payload))
        print(f"report {payload['report']}", flush=True)
        print("dry-run. pass --execute to rename and relink.", flush=True)
        print(
            "after --execute, remap Traktor / Rekordbox with music_migration "
            "using remaps[] in the report. Keep Music Media folder organized Off.",
            flush=True,
        )
        return payload

    applied = 0
    failed = 0
    results = []
    for item in moves:
        result = apply_move(item, media_root=root, set_location=set_location)
        results.append({**asdict(item), **result})
        if result["ok"]:
            applied += 1
            print(f"ok {item.reason} {Path(item.source).name} -> {Path(item.dest).name}", flush=True)
        else:
            failed += 1
            print(
                f"moved-unlinked {item.source} -> {item.dest} ({result['error']})",
                flush=True,
            )
    payload["executed"] = True
    payload["applied"] = applied
    payload["relink_failed"] = failed
    payload["results"] = results
    payload["report"] = str(write_report(payload))
    print(f"applied {applied}  relink_failed {failed}", flush=True)
    print(f"report {payload['report']}", flush=True)
    print(
        "remap Traktor / Rekordbox with music_migration using remaps[] in the report.",
        flush=True,
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(
            execute=args.execute,
            playlist=args.playlist,
            limit=args.limit,
            media_root=args.media_root,
        )
    except (MusicDupesError, OrganizeError) as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
