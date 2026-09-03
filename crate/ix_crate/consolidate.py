"""Bring audio off a migration drive onto the internal disk.

A previous migration moved audio out of ``~`` onto an external volume, which
is why so many library rows lost their file. This walks a source tree, drops
anything already held locally, and files the rest under ``~/Music`` by
**Artist / Album** using tags rather than the source layout — the exFAT copy
truncated filenames and rewrote ``/`` as ``_``, so source paths are not
trustworthy but tags survived.

Copies only. Nothing on the source is moved or deleted, and nothing already
under ``~/Music`` is overwritten, so a run can be repeated safely.

Duplicate test is exact byte size plus normalized title. Size alone collides
across an encode of the same length; title alone collides across
compilations. Together they are strong enough to avoid hashing 300GB over
USB, and a size tie with a matching title is confirmed by hashing just that
pair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .families import is_audio
from .identify import _read_tags, normalize_title, sanitize, strip_track_number
from .paths import (
    APPLE_MEDIA_SKIP_DIRS,
    APPLE_MUSIC,
    REPORTS,
    ROLE_SUFFIXES,
    STEM_SUFFIXES,
    STEMS_AUDIO,
)

# DJ and DAW application state. Sample content, project scratch and record
# boxes, none of it belongs in the library.
SKIP_DIRS = {
    "_Serato_",
    "_Serato_.blarg",
    "_Serato_Backup",
    "Serato Studio",
    "Ableton",
    "Logic",
    "Audio Music Apps",
    "PioneerDJ",
    "Traktor",
    "Traktor 4.4.2",
    "rekordbox",
    "rekordbox_db_old",
    "rekordbox_old_prefs",
    "Density",
    "Recording",
    "Previous Libraries.localized",
    "Music Library.musiclibrary",
    ".Trashes",
    "$RECYCLE.BIN",
    "System Volume Information",
}
HASH_BYTES = 4 * 1024 * 1024
UNKNOWN_ARTIST_NAME = "Unknown Artist"
UNKNOWN_ALBUM_NAME = "Unknown Album"


class ConsolidateError(RuntimeError):
    pass


@dataclass
class Candidate:
    source: Path
    dest: Path
    artist: str
    album: str
    title: str
    size: int


@dataclass
class ConsolidatePlan:
    copy: list[Candidate] = field(default_factory=list)
    duplicate: int = 0
    skipped: int = 0
    scanned: int = 0
    bytes_to_copy: int = 0
    by_artist: dict[str, int] = field(default_factory=dict)


def assert_within(path: Path, root: Path) -> Path:
    """A planned write must land inside the root it was planned against."""
    resolved = Path(os.path.normpath(str(path.expanduser())))
    base = Path(os.path.normpath(str(root.expanduser())))
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ConsolidateError(f"refusing to write outside {base}: {path}") from exc
    return resolved


def assert_under_music(path: Path) -> Path:
    """Roots this command may target at all. Checked once, not per file."""
    return assert_within(path, Path.home() / "Music")


def is_stem(path: Path) -> bool:
    low = path.name.lower()
    if any(low.endswith(suffix) for suffix in STEM_SUFFIXES):
        return True
    stem = low.rsplit(".", 1)[0]
    return any(stem.endswith(f"_{role}") or stem.endswith(f" {role}") for role in ROLE_SUFFIXES)


def walk_audio(root: Path) -> Iterable[Path]:
    """Audio under ``root``, minus app state and AppleDouble stubs."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            if name.startswith("._"):
                continue
            path = base / name
            if is_audio(path):
                yield path


def title_of(path: Path, tag_title: str) -> str:
    return normalize_title(tag_title or strip_track_number(path.stem))


def index_local(roots: Iterable[Path], on_progress=None) -> dict[tuple[int, str], list[Path]]:
    """(size, normalized title) -> local paths already holding that audio."""
    index: dict[tuple[int, str], list[Path]] = defaultdict(list)
    count = 0
    for root in roots:
        root = root.expanduser()
        if not root.is_dir():
            continue
        for path in walk_audio(root):
            try:
                size = path.stat().st_size
            except OSError:
                continue
            _, _, tag_title = _read_tags(path)
            index[(size, title_of(path, tag_title))].append(path)
            count += 1
            if on_progress and count % 2000 == 0:
                on_progress(count)
    if on_progress:
        on_progress(count)
    return index


def _head_digest(path: Path) -> str:
    digest = hashlib.sha1()
    try:
        with path.open("rb") as handle:
            digest.update(handle.read(HASH_BYTES))
    except OSError:
        return ""
    return digest.hexdigest()


def same_audio(left: Path, right: Path) -> bool:
    """Confirm a size+title tie by comparing the leading bytes."""
    a = _head_digest(left)
    return bool(a) and a == _head_digest(right)


def destination(path: Path, dest_root: Path, stems_root: Path) -> tuple[Path, str, str, str]:
    artist, album, title = _read_tags(path)
    display_title = title or strip_track_number(path.stem)
    root = stems_root if is_stem(path) else dest_root
    folder = root / sanitize(artist, UNKNOWN_ARTIST_NAME) / sanitize(album, UNKNOWN_ALBUM_NAME)
    return folder / path.name, artist, album, display_title


def unique_dest(dest: Path, taken: set[Path]) -> Path:
    """Never overwrite. Suffix a name that is already spoken for."""
    if dest not in taken and not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    for n in range(2, 100):
        candidate = dest.with_name(f"{stem} ({n}){suffix}")
        if candidate not in taken and not candidate.exists():
            return candidate
    raise ConsolidateError(f"cannot find a free name for {dest}")


def build_plan(
    sources: Iterable[Path],
    local_index: dict[tuple[int, str], list[Path]],
    *,
    dest_root: Path,
    stems_root: Path,
    on_progress=None,
) -> ConsolidatePlan:
    plan = ConsolidatePlan()
    taken: set[Path] = set()
    for source_root in sources:
        source_root = source_root.expanduser()
        if not source_root.is_dir():
            raise ConsolidateError(f"no such source {source_root}")
        for path in walk_audio(source_root):
            plan.scanned += 1
            if on_progress and plan.scanned % 500 == 0:
                on_progress(plan.scanned, plan.copy and len(plan.copy) or 0)
            try:
                size = path.stat().st_size
            except OSError:
                plan.skipped += 1
                continue
            dest, artist, album, title = destination(path, dest_root, stems_root)
            key = (size, title_of(path, title))
            matches = local_index.get(key)
            if matches and any(same_audio(path, other) for other in matches):
                plan.duplicate += 1
                continue
            root = stems_root if is_stem(path) else dest_root
            dest = unique_dest(assert_within(dest, root), taken)
            taken.add(dest)
            plan.copy.append(
                Candidate(
                    source=path,
                    dest=dest,
                    artist=artist,
                    album=album,
                    title=title,
                    size=size,
                )
            )
            plan.bytes_to_copy += size
            label = sanitize(artist, UNKNOWN_ARTIST_NAME)
            plan.by_artist[label] = plan.by_artist.get(label, 0) + 1
    return plan


def copy_one(item: Candidate) -> bool:
    """Copy preserving mtime, verifying size, leaving no partial file behind."""
    item.dest.parent.mkdir(parents=True, exist_ok=True)
    temp = item.dest.with_name(item.dest.name + ".partial")
    try:
        shutil.copy2(item.source, temp)
        if temp.stat().st_size != item.size:
            temp.unlink(missing_ok=True)
            return False
        temp.replace(item.dest)
    except OSError:
        temp.unlink(missing_ok=True)
        return False
    return True


def execute(plan: ConsolidatePlan, *, on_progress=None) -> tuple[int, int, int]:
    copied = failed = 0
    moved_bytes = 0
    for i, item in enumerate(plan.copy, start=1):
        if copy_one(item):
            copied += 1
            moved_bytes += item.size
        else:
            failed += 1
        if on_progress and (i % 25 == 0 or i == len(plan.copy)):
            on_progress(i, len(plan.copy), moved_bytes)
    return copied, failed, moved_bytes


def _gb(value: int) -> float:
    return round(value / (1024**3), 2)


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"consolidate-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate consolidate",
        description="Copy audio from a migration drive into ~/Music by artist/album.",
    )
    parser.add_argument("sources", nargs="+", type=Path, help="source roots to walk")
    parser.add_argument("--execute", action="store_true", help="perform the copies")
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help=f"library root (default {APPLE_MUSIC})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dest_root = assert_under_music((args.dest or APPLE_MUSIC).expanduser())
    stems_root = assert_under_music(STEMS_AUDIO.expanduser())

    print(f"index local {dest_root}", flush=True)
    local_index = index_local(
        [dest_root, stems_root],
        on_progress=lambda n: print(f"  local {n}", flush=True),
    )
    print(f"local audio keys {len(local_index)}", flush=True)

    plan = build_plan(
        args.sources,
        local_index,
        dest_root=dest_root,
        stems_root=stems_root,
        on_progress=lambda n, c: print(f"  scan {n} ({c} to copy)", flush=True),
    )

    print(
        f"scanned {plan.scanned}  copy {len(plan.copy)}  "
        f"duplicate {plan.duplicate}  skipped {plan.skipped}  "
        f"{_gb(plan.bytes_to_copy)} GB",
        flush=True,
    )
    top = sorted(plan.by_artist.items(), key=lambda kv: -kv[1])[:15]
    for artist, count in top:
        print(f"  {count:5}  {artist}", flush=True)

    report = write_report(
        {
            "scanned": plan.scanned,
            "copy": len(plan.copy),
            "duplicate": plan.duplicate,
            "skipped": plan.skipped,
            "gb": _gb(plan.bytes_to_copy),
            "executed": bool(args.execute),
            "plan": [
                {
                    "source": str(item.source),
                    "dest": str(item.dest),
                    "artist": item.artist,
                    "album": item.album,
                    "title": item.title,
                    "size": item.size,
                }
                for item in plan.copy
            ],
        }
    )
    print(f"report {report}", flush=True)

    if not args.execute:
        print("dry run, nothing copied. re-run with --execute", flush=True)
        return 0

    free = shutil.disk_usage(dest_root).free
    if free < plan.bytes_to_copy * 1.05:
        print(
            f"not enough room: need {_gb(plan.bytes_to_copy)} GB, have {_gb(free)} GB",
            flush=True,
        )
        return 2

    def progress(done: int, total: int, moved: int) -> None:
        print(f"copy {done}/{total}  {_gb(moved)} GB", flush=True)

    copied, failed, moved = execute(plan, on_progress=progress)
    print(f"copied {copied}  failed {failed}  {_gb(moved)} GB", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
