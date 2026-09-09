"""Restore WAV/AIFF files that had ID3 prepended, then drop Finder copies.

``music-fix`` wrote EasyID3 / ``ID3().save`` onto ``.wav`` files. That
puts ``ID3`` where ``RIFF`` belongs, so Music.app and ffmpeg refuse the
file. ``consolidate`` then copied the still-valid Terrarum original in as
``Track (2).wav`` (and a later pass as ``(3)``) because the bloated
corrupt file no longer matched on size.

This walks a folder (recursively), groups ``Name.wav`` / ``Name (2).wav``
in the same directory, keeps the unnumbered name, copies a valid RIFF
(local sibling or ``--source``) over it when the unnumbered file is
corrupt, and deletes extras only when decoded audio matches the keeper.

Music.app rows that pointed at a deleted ``(2)``/``(3)`` are relinked to
the keeper. Dry-run is the default.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .music_dupes import MusicDupesError, _run_osascript, count_file_tracks
from .music_repair import strip_copy_suffix
from .music_replicants import decoded_digest
from .paths import APPLE_MUSIC, REPORTS

JUNK_SUFFIX = {".pkf"}
AUDIO_SUFFIX = {".wav", ".aiff", ".aif"}
DEFAULT_FOLDER = APPLE_MUSIC
DEFAULT_SOURCE = Path(
    "/Volumes/Terrarum/MIGRATION_MASTER/Music/Music/Media.localized"
)


class RiffRepairError(RuntimeError):
    pass


@dataclass
class Member:
    path: Path
    number: int
    riff: bool
    digest: str = ""


@dataclass
class GroupFix:
    key: str
    keeper: Path | None
    restore_from: Path | None = None
    delete: list[Path] = field(default_factory=list)
    missing: bool = False


def is_riff(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(4) == b"RIFF"
    except OSError:
        return False


def is_form(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(4) == b"FORM"
    except OSError:
        return False


def is_id3_headed(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(3) == b"ID3"
    except OSError:
        return False


def copy_number(stem: str) -> int:
    """``Track (2)`` → 2. Unnumbered → 0."""
    if stem.endswith(")") and "(" in stem:
        tail = stem.rsplit("(", 1)[1].rstrip(")")
        if tail.isdigit():
            return int(tail)
    return 0


FINDER_COPY_MAX = 12


def finder_copy_number(path: Path) -> int:
    """Finder ``(2)`` including ``.stem (2).m4a`` and ``Title (2).stem.m4a``.

    Years like ``(1999)`` stay 0.
    """
    from ix_crate.paths import STEM_SUFFIXES

    numbered = copy_number(path.stem)
    if 0 < numbered <= FINDER_COPY_MAX:
        return numbered
    lower = path.name.lower()
    for suffix in STEM_SUFFIXES:
        if lower.endswith(suffix):
            numbered = copy_number(path.name[: -len(suffix)])
            if 0 < numbered <= FINDER_COPY_MAX:
                return numbered
            break
    return 0


def group_key(path: Path) -> str:
    """Same directory + unnumbered stem + suffix. Album folders stay distinct."""
    return f"{path.parent}\t{strip_copy_suffix(path.stem).lower()}\t{path.suffix.lower()}"


def list_audio(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.rglob("*")
        if p.is_file()
        and not p.name.startswith(".")
        and not p.name.startswith("._")
        and p.suffix.lower() in AUDIO_SUFFIX
    )


def list_junk(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in JUNK_SUFFIX
    )


def is_playable(path: Path) -> bool:
    """WAV/AIFF must still be RIFF/FORM. Other audio is playable if it decodes."""
    suf = path.suffix.lower()
    if suf == ".wav":
        return is_riff(path)
    if suf in {".aiff", ".aif"}:
        return is_form(path)
    return bool(path.is_file() and path.stat().st_size > 0)


def source_match(source: Path, keeper: Path, folder: Path) -> Path | None:
    """Find a playable original under ``source`` for ``keeper``."""
    if not source.is_dir():
        return None
    try:
        rel = keeper.relative_to(folder)
    except ValueError:
        rel = Path(keeper.name)
    candidates = [source / rel, source / "Music" / rel]
    if rel.parts and rel.parts[0] == "Music":
        candidates.append(source / Path(*rel.parts[1:]))
    candidates.append(source / keeper.name)
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file() and is_playable(candidate):
            return candidate
    return None


def _digest(path: Path, cache: dict[str, str]) -> str:
    key = str(path)
    if key not in cache:
        cache[key] = decoded_digest(path) if is_playable(path) else ""
    return cache[key]


def plan_group(
    paths: list[Path],
    *,
    source: Path | None = None,
    folder: Path | None = None,
    cache: dict[str, str] | None = None,
) -> GroupFix:
    cache = cache if cache is not None else {}
    members = [
        Member(path=p, number=copy_number(p.stem), riff=is_playable(p)) for p in paths
    ]
    members.sort(key=lambda m: (m.number, str(m.path)))
    key = group_key(paths[0])
    canonical = paths[0].with_name(
        strip_copy_suffix(paths[0].stem) + paths[0].suffix
    )
    valid = [m for m in members if m.riff]
    if not valid:
        remote = (
            source_match(source, canonical, folder)
            if source is not None and folder is not None
            else None
        )
        if remote is None:
            return GroupFix(key=key, keeper=None, missing=True)
        return GroupFix(
            key=key,
            keeper=canonical,
            restore_from=remote,
            delete=[m.path for m in members if m.path != canonical],
        )

    for m in valid:
        m.digest = _digest(m.path, cache)
    valid = [m for m in valid if m.digest]
    if not valid:
        return GroupFix(key=key, keeper=None, missing=True)

    # Prefer the unnumbered name as keeper; restore it from a valid sibling
    # when the unnumbered file itself does not decode.
    numbered_ok = [m for m in valid if m.number == 0]
    donor = numbered_ok[0] if numbered_ok else valid[0]
    keeper = canonical
    restore = None if (canonical.exists() and is_playable(canonical) and canonical == donor.path) else donor.path
    keeper_digest = donor.digest
    extras = []
    for m in members:
        if m.path == keeper:
            continue
        if m.path == restore:
            extras.append(m.path)
            continue
        if m.riff and _digest(m.path, cache) == keeper_digest:
            extras.append(m.path)
            continue
        if not m.riff:
            extras.append(m.path)
    return GroupFix(key=key, keeper=keeper, restore_from=restore, delete=extras)


def build_plan(
    folder: Path, *, source: Path | None = None, on_progress=None
) -> tuple[list[GroupFix], list[Path]]:
    cache: dict[str, str] = {}
    buckets: dict[str, list[Path]] = defaultdict(list)
    files = list_audio(folder)
    for path in files:
        buckets[group_key(path)].append(path)
    items: list[GroupFix] = []
    work = [
        paths
        for paths in buckets.values()
        if len(paths) > 1 or (paths and not is_playable(paths[0]))
    ]
    total = len(work)
    for i, paths in enumerate(sorted(work, key=lambda p: str(p[0])), start=1):
        items.append(plan_group(paths, source=source, folder=folder, cache=cache))
        if on_progress and i % 10 == 0:
            on_progress(i, total)
    if on_progress:
        on_progress(total, total)
    return items, list_junk(folder)


def apply_group(fix: GroupFix) -> None:
    if fix.keeper is None:
        return
    if fix.restore_from is not None:
        temp = fix.keeper.with_name(fix.keeper.name + ".partial")
        shutil.copy2(fix.restore_from, temp)
        if not is_playable(temp):
            temp.unlink(missing_ok=True)
            raise RiffRepairError(f"restore was not RIFF: {fix.restore_from}")
        temp.replace(fix.keeper)
    for extra in fix.delete:
        extra.unlink(missing_ok=True)


def dump_locations(folder: Path) -> dict[str, str]:
    """persistent ID → POSIX path for rows whose file sits in ``folder``."""
    folder_s = str(folder.resolve())
    found: dict[str, str] = {}
    total = count_file_tracks()
    start = 1
    while start <= total:
        end = min(start + 999, total)
        script = f"""
tell application "Music"
  set pids to (persistent ID of file tracks {start} thru {end} of library playlist 1) as list
  set locs to (location of file tracks {start} thru {end} of library playlist 1) as list
  set out to ""
  repeat with i from 1 to count of pids
    set h to ""
    try
      set h to POSIX path of (item i of locs)
    end try
    set out to out & (item i of pids as text) & tab & h & linefeed
  end repeat
  return out
end tell
"""
        for line in _run_osascript(script, timeout=300).splitlines():
            if not line.strip():
                continue
            pid, path = (line.split("\t") + ["", ""])[:2]
            path = path.strip()
            if pid and path.startswith(folder_s):
                found[pid.strip()] = path
        start = end + 1
    return found


def relink(pid: str, path: Path) -> None:
    from .music_repair import set_track_location

    set_track_location(pid, path)


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"riff-repair-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate riff-repair",
        description="Restore ID3-corrupted WAVs in a folder and drop Finder copies.",
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=DEFAULT_FOLDER,
        help="folder to clean (default: Media.localized, recursive)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Terrarum (or other) folder holding valid originals",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    folder = args.folder.expanduser()
    source = args.source.expanduser() if args.source else None
    if not folder.is_dir():
        raise SystemExit(f"not a folder: {folder}")

    print(f"folder {folder}", flush=True)
    items, junk = build_plan(
        folder,
        source=source if source and source.is_dir() else None,
        on_progress=lambda d, t: print(f"hash {d}/{t}", flush=True),
    )
    restore = [g for g in items if g.restore_from]
    delete_n = sum(len(g.delete) for g in items) + len(junk)
    missing = [g for g in items if g.missing]
    print(
        f"groups {len(items)}  restore {len(restore)}  "
        f"delete {delete_n}  missing {len(missing)}",
        flush=True,
    )
    for g in restore[: args.limit]:
        print(f"  restore {g.keeper.name}  from {g.restore_from.name}", flush=True)
    for g in missing[: args.limit]:
        print(f"  missing {g.key}", flush=True)

    payload = {
        "folder": str(folder),
        "groups": len(items),
        "restore": len(restore),
        "delete": delete_n,
        "missing": len(missing),
        "executed": False,
        "restores": [
            {"keeper": str(g.keeper), "from": str(g.restore_from), "delete": [str(p) for p in g.delete]}
            for g in restore
        ],
        "missing_keys": [g.key for g in missing],
    }
    if not args.execute:
        report = write_report(payload)
        print(f"report {report}", flush=True)
        print("dry run, nothing changed. re-run with --execute", flush=True)
        return 0

    deleted: dict[str, Path] = {}
    for g in items:
        if g.keeper is None:
            continue
        for extra in g.delete:
            deleted[str(extra.resolve())] = g.keeper
        apply_group(g)
    for peak in junk:
        peak.unlink(missing_ok=True)
    print("files rewritten", flush=True)

    try:
        rows = dump_locations(folder)
    except MusicDupesError as exc:
        print(f"library scan skipped: {exc}", flush=True)
        rows = {}
    relinked = 0
    for pid, path in rows.items():
        keeper = deleted.get(str(Path(path).resolve()))
        if keeper is None or not keeper.is_file():
            continue
        try:
            relink(pid, keeper)
            relinked += 1
        except MusicDupesError as exc:
            print(f"relink skip {pid}: {exc}", flush=True)
    payload["executed"] = True
    payload["relinked"] = relinked
    report = write_report(payload)
    print(f"relinked {relinked}  report {report}", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
