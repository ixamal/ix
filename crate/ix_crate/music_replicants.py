"""Drop library rows that duplicate a recording held under a second filename.

``music-dupes`` groups rows by path and catches several rows sharing one
file. It cannot see the other shape: two rows, two files, identical audio.
iTunes writes a second copy as ``Track 1.m4a``, and consolidating the
migration drive added more, because a title key of ``track 1`` does not
match ``track``.

Grouping is by artist/album/title, but nothing is deleted on a name match
alone. Every file in a group must decode to the same audio (or, for DRM
that will not decode, the same leading bytes). A group that disagrees is
reported and left alone — alternate takes and different masters share a
title legitimately.

Rows in playlists are preferred as keepers so a cleanup never empties a
crate slot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .identify import normalize_title
from .music_dupes import (
    MusicDupesError,
    TrackRow,
    canon_path,
    delete_library_row,
    scan_library,
)
from .music_repair import fold_artist, strip_copy_suffix
from .paths import REPORTS

HASH_BYTES = 1024 * 1024


class ReplicantError(RuntimeError):
    pass


@dataclass
class Twins:
    """One recording held by several library rows via different files."""

    key: tuple[str, str, str]
    keep: TrackRow
    extras: list[TrackRow] = field(default_factory=list)
    reclaim: int = 0


@dataclass
class Plan:
    twins: list[Twins] = field(default_factory=list)
    mismatched: int = 0
    scanned: int = 0

    @property
    def extra_rows(self) -> int:
        return sum(len(t.extras) for t in self.twins)

    @property
    def reclaim(self) -> int:
        return sum(t.reclaim for t in self.twins)


def identity(row: TrackRow) -> tuple[str, str, str]:
    return (
        fold_artist(row.artist),
        normalize_title(row.album),
        normalize_title(strip_copy_suffix(row.name)),
    )


def _byte_digest(path: Path) -> str:
    try:
        stat = path.stat()
        with path.open("rb") as handle:
            head = hashlib.sha1(handle.read(HASH_BYTES)).hexdigest()
        return f"bytes:{stat.st_size}:{head}"
    except OSError:
        return ""


def decoded_digest(path: Path) -> str:
    """MD5 of the decoded audio stream, ignoring tags.

    Comparing raw bytes finds almost nothing here. A track Music.app has
    re-tagged differs from its own copy by a few dozen bytes of metadata
    while the audio is untouched, so a byte test called 895 real duplicates
    distinct. Decoding to mono 22 kHz costs 0.2s a file and compares what we
    actually mean by "the same recording".
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-v", "quiet", "-i", str(path), "-map", "0:a:0",
             "-ac", "1", "-ar", "22050", "-f", "md5", "-"],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    out = (result.stdout or "").strip()
    if not out.startswith("MD5="):
        return ""
    # Some of these rips make ffmpeg exit nonzero on a trailing bad frame while
    # still decoding and hashing the audio. Demanding a clean exit threw away
    # pairs whose hashes agreed exactly. The duration is folded in so a hash
    # covering a partial decode can never equate two tracks of different length.
    return f"audio:{track_seconds(path)}:{out}"


def track_seconds(path: Path) -> str:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return f"{float((result.stdout or '0').strip()):.1f}"
    except (OSError, ValueError, subprocess.SubprocessError):
        return "?"


def fingerprint(path: Path, cache: dict[str, str] | None = None) -> str:
    """Decoded audio where possible, raw bytes for DRM that will not decode."""
    key = str(path)
    if cache is not None and key in cache:
        return cache[key]
    value = decoded_digest(path) or _byte_digest(path)
    if cache is not None:
        cache[key] = value
    return value


def same_audio(paths: list[Path], cache: dict[str, str] | None = None) -> bool:
    if len(paths) < 2:
        return False
    prints = {fingerprint(p, cache) for p in paths}
    return len(prints) == 1 and "" not in prints


def _marker_penalty(path: Path) -> int:
    """Prefer the original filename over a duplicate copy's."""
    stem = path.stem
    if stem.endswith(")") and "(" in stem:
        tail = stem.rsplit("(", 1)[1].rstrip(")")
        if tail.isdigit():
            return 2
    parts = stem.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return 1
    return 0


def choose_keeper(rows: list[TrackRow]) -> TrackRow:
    """Playlist membership first, then plays and rating, then the cleanest
    filename, then the oldest library row."""

    def rank(row: TrackRow) -> tuple:
        path = Path(canon_path(row.location) or row.location)
        return (
            -row.playlist_hits,
            -row.played_count,
            -row.rating,
            _marker_penalty(path),
            row.database_id,
        )

    return sorted(rows, key=rank)[0]


def build_plan(
    rows: Iterable[TrackRow], *, scanned: int = 0, on_progress=None
) -> Plan:
    plan = Plan(scanned=scanned)
    cache: dict[str, str] = {}
    buckets: dict[tuple[str, str, str], list[TrackRow]] = defaultdict(list)
    for row in rows:
        key = identity(row)
        if not key[2]:
            continue
        buckets[key].append(row)

    candidates = sorted((k, v) for k, v in buckets.items() if len(v) > 1)
    for done, (key, members) in enumerate(candidates, start=1):
        if on_progress and done % 25 == 0:
            on_progress(done, len(candidates))
        live = [m for m in members if canon_path(m.location)]
        paths = [Path(canon_path(m.location)) for m in live]
        if len(live) < 2 or not all(p.is_file() for p in paths):
            continue
        if len({str(p) for p in paths}) < 2:
            continue  # same file, several rows: that is music-dupes' job
        if not same_audio(paths, cache):
            plan.mismatched += 1
            continue
        keep = choose_keeper(live)
        extras = [m for m in live if m.persistent_id != keep.persistent_id]
        reclaim = 0
        for extra in extras:
            try:
                reclaim += Path(canon_path(extra.location)).stat().st_size
            except OSError:
                pass
        plan.twins.append(Twins(key=key, keep=keep, extras=extras, reclaim=reclaim))
    return plan


def drop_extra(row: TrackRow, keeper: Path) -> dict[str, Any]:
    """Delete one duplicate row, refusing to proceed if the kept copy moved.

    Music.app may bin the row's own file. That is acceptable here and only
    here: the audio was verified identical (decoded, or leading bytes for
    DRM) to the copy we keep, so nothing is lost. The kept file is
    re-checked after every delete.
    """
    if not keeper.is_file():
        raise ReplicantError(f"kept file vanished before delete: {keeper}")
    path = Path(canon_path(row.location) or row.location)
    delete_library_row(row.persistent_id)
    if not keeper.is_file():
        raise ReplicantError(
            f"Music.app removed the kept audio while deleting a duplicate row. "
            f"Stopped. kept={keeper} deleted_row={row.persistent_id}"
        )
    return {
        "persistent_id": row.persistent_id,
        "dropped_file": str(path),
        "file_still_present": path.is_file(),
    }


def execute(plan: Plan, *, on_progress=None) -> tuple[int, int]:
    dropped = failed = 0
    total = plan.extra_rows
    for group in plan.twins:
        keeper = Path(canon_path(group.keep.location))
        for extra in group.extras:
            try:
                drop_extra(extra, keeper)
                dropped += 1
            except (ReplicantError, MusicDupesError) as exc:
                print(f"stop: {exc}", flush=True)
                return dropped, failed + 1
            if on_progress and (dropped + failed) % 25 == 0:
                on_progress(dropped + failed, total)
    if on_progress:
        on_progress(dropped + failed, total)
    return dropped, failed


def _mb(value: int) -> float:
    return round(value / (1024**2), 1)


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"music-replicants-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate music-replicants",
        description="Drop library rows duplicating a recording held twice on disk.",
    )
    parser.add_argument("--execute", action="store_true", help="delete the extra rows")
    parser.add_argument(
        "--limit", type=int, default=25, help="how many groups to print"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    rows, file_tracks = scan_library(
        on_scan=lambda d, t: print(f"scan {d}/{t}", flush=True),
        on_playlists=lambda d, t: print(f"playlists {d}/{t}", flush=True),
    )
    plan = build_plan(
        rows,
        scanned=file_tracks,
        on_progress=lambda d, t: print(f"hash {d}/{t}", flush=True),
    )

    print(
        f"scanned {plan.scanned}  duplicate recordings {len(plan.twins)}  "
        f"extra rows {plan.extra_rows}  reclaimable {_mb(plan.reclaim)} MB",
        flush=True,
    )
    print(
        f"same title but genuinely different audio, left alone: {plan.mismatched}",
        flush=True,
    )
    for group in plan.twins[: args.limit]:
        artist, _, title = group.key
        print(f"  {artist[:24]:26} | {title[:38]:40} x{len(group.extras) + 1}")
        print(f"     keep {Path(canon_path(group.keep.location)).name[:74]}")
        for extra in group.extras:
            print(f"     drop {Path(canon_path(extra.location)).name[:74]}")

    payload = {
        "scanned": plan.scanned,
        "groups": len(plan.twins),
        "extra_rows": plan.extra_rows,
        "reclaimable_mb": _mb(plan.reclaim),
        "mismatched": plan.mismatched,
        "executed": False,
        "groups_detail": [
            {
                "artist": g.key[0],
                "album": g.key[1],
                "title": g.key[2],
                "keep": canon_path(g.keep.location),
                "drop": [canon_path(e.location) for e in g.extras],
            }
            for g in plan.twins
        ],
    }

    if not args.execute:
        report = write_report(payload)
        print(f"report {report}", flush=True)
        print("dry run, nothing deleted. re-run with --execute", flush=True)
        return 0

    dropped, failed = execute(
        plan, on_progress=lambda d, t: print(f"drop {d}/{t}", flush=True)
    )
    payload["executed"] = True
    payload["dropped"] = dropped
    payload["failed"] = failed
    report = write_report(payload)
    print(f"report {report}", flush=True)
    print(f"dropped {dropped} rows  failed {failed}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
