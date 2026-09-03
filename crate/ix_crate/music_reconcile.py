"""Relink Music.app rows that lost their file.

Music.app reports ``missing value`` for a row whose file it can no longer
resolve. It does not remember the old path, but the 2021 ``iTunes Music
Library.xml`` does, keyed by the same persistent ID the live library still
uses. That map turns a fuzzy title search into an exact per-row lookup.

Two passes:

internal
    Point each dead row back at its own recorded file under Media.localized.
    Also tries the path with the ``Music/`` container removed, because rows
    written while that container was a symlink to ``.`` record a path one
    level deeper than where the file actually sits.

external
    For rows whose recorded file is gone, rebase the recorded path onto a
    backup Media.localized tree (same layout, different root), then fall back
    to artist/title matching over the rest of the external root.

A candidate is only used when no live row already holds it, so a relink can
never mint a duplicate row.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

from .music_dupes import _run_osascript, count_file_tracks
from .music_repair import RepairRow, _quote_as, index_tree, pick_match
from .paths import APPLE_MUSIC, REPORTS

MEDIA_SEGMENT = "/Media.localized/"
MUSIC_SEGMENT = "/Media.localized/Music/"
# osascript grows quadratically slow on huge literals; this stays well under.
BATCH = 200


class ReconcileError(RuntimeError):
    pass


@dataclass
class DeadRow:
    """A library row whose file Music.app cannot resolve."""

    index: int
    persistent_id: str
    artist: str = ""
    album: str = ""
    name: str = ""
    duration: float = 0.0


@dataclass
class Relink:
    row: DeadRow
    path: Path
    reason: str


@dataclass
class Plan:
    relink: list[Relink] = field(default_factory=list)
    duplicate: list[DeadRow] = field(default_factory=list)
    unresolved: list[DeadRow] = field(default_factory=list)
    scanned: int = 0
    live: int = 0


def xml_path() -> Path:
    return APPLE_MUSIC.expanduser() / "iTunes Music Library.xml"


def xml_locations(path: Path | None = None) -> dict[str, str]:
    """Persistent ID -> POSIX path, as recorded in the iTunes XML export."""
    source = path or xml_path()
    if not source.is_file():
        raise ReconcileError(
            f"no iTunes XML at {source}. Music > Settings > Advanced > "
            "Share Library XML with other applications."
        )
    with source.open("rb") as handle:
        data = plistlib.load(handle)
    out: dict[str, str] = {}
    for track in data.get("Tracks", {}).values():
        pid = track.get("Persistent ID")
        loc = track.get("Location")
        if pid and loc:
            out[pid] = unquote(str(loc).replace("file://", ""))
    return out


def hoist(path: str) -> str | None:
    """Drop the ``Music/`` copy container from a recorded path."""
    if MUSIC_SEGMENT not in path:
        return None
    return path.replace(MUSIC_SEGMENT, MEDIA_SEGMENT, 1)


def rebase(path: str, root: Path) -> list[str]:
    """Map a recorded Media.localized path onto another Media.localized root."""
    if MEDIA_SEGMENT not in path:
        return []
    tail = path.split(MEDIA_SEGMENT, 1)[1]
    out = [str(root / tail)]
    if tail.startswith("Music/"):
        out.append(str(root / tail[len("Music/") :]))
    return out


def scan_library(on_progress=None) -> tuple[list[DeadRow], set[str], int]:
    """Walk the library positionally, splitting rows into dead and live.

    Reads ``location`` in bulk. The per-track form (``location of t`` inside a
    repeat) fails to coerce on this library and reports every row as dead.
    """
    total = count_file_tracks()
    dead: list[DeadRow] = []
    claimed: set[str] = set()
    start = 1
    while start <= total:
        end = min(start + BATCH * 2 - 1, total)
        script = f"""
tell application "Music"
  set pids to persistent ID of file tracks {start} thru {end} of library playlist 1
  set nms to name of file tracks {start} thru {end} of library playlist 1
  set ars to artist of file tracks {start} thru {end} of library playlist 1
  set als to album of file tracks {start} thru {end} of library playlist 1
  set durs to duration of file tracks {start} thru {end} of library playlist 1
  set locs to location of file tracks {start} thru {end} of library playlist 1
  set out to ""
  repeat with i from 1 to count of pids
    set h to ""
    try
      set h to POSIX path of (item i of locs)
    end try
    set out to out & (item i of pids as text) & tab & h & tab & (item i of ars as text) & tab & (item i of als as text) & tab & (item i of nms as text) & tab & (item i of durs as text) & linefeed
  end repeat
  return out
end tell
"""
        offset = start
        for line in _run_osascript(script, timeout=300).splitlines():
            if not line.strip():
                continue
            parts = (line.split("\t") + [""] * 6)[:6]
            pid, posix, artist, album, name, duration = (p.strip() for p in parts)
            if not pid:
                continue
            if posix:
                claimed.add(posix)
            else:
                dead.append(
                    DeadRow(
                        index=offset,
                        persistent_id=pid,
                        artist=artist,
                        album=album,
                        name=name,
                        duration=_as_float(duration),
                    )
                )
            offset += 1
        if on_progress:
            on_progress(min(end, total), total)
        start = end + 1
    return dead, claimed, total


def _as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_repair_row(row: DeadRow) -> RepairRow:
    return RepairRow(
        persistent_id=row.persistent_id,
        database_id=0,
        artist=row.artist,
        album=row.album,
        name=row.name,
        genre="",
        duration=row.duration,
        location="",
    )


def build_plan(
    dead: Iterable[DeadRow],
    claimed: set[str],
    locations: dict[str, str],
    *,
    external: Path | None = None,
    external_index: dict[str, Any] | None = None,
) -> Plan:
    """Choose one unclaimed file per dead row, preferring exact recorded paths."""
    plan = Plan()
    taken = set(claimed)
    for row in dead:
        recorded = locations.get(row.persistent_id)
        choice: tuple[str, str] | None = None
        if recorded:
            for cand, reason in _internal_candidates(recorded):
                if cand in taken:
                    choice = ("", "duplicate")
                    break
                if Path(cand).is_file():
                    choice = (cand, reason)
                    break
        if choice is None and recorded and external is not None:
            for cand in rebase(recorded, external):
                if cand not in taken and Path(cand).is_file():
                    choice = (cand, "external:rebase")
                    break
        if choice is None and external_index is not None:
            match, reason = pick_match(_as_repair_row(row), external_index)
            if match is not None and str(match) not in taken:
                choice = (str(match), f"external:{reason}")
        if choice is None:
            plan.unresolved.append(row)
            continue
        cand, reason = choice
        if reason == "duplicate":
            plan.duplicate.append(row)
            continue
        taken.add(cand)
        plan.relink.append(Relink(row=row, path=Path(cand), reason=reason))
    return plan


def _internal_candidates(recorded: str) -> list[tuple[str, str]]:
    out = [(recorded, "xml:recorded")]
    lifted = hoist(recorded)
    if lifted:
        out.append((lifted, "xml:hoisted"))
    return out


def apply_relinks(items: list[Relink], *, on_progress=None) -> tuple[int, int]:
    """Set locations positionally, confirming the persistent ID at each index.

    Positional access avoids a whole-library ``whose`` search per row, which is
    the difference between minutes and hours at this scale. The ID check is
    what makes it safe if the row order ever shifts underneath us.
    """
    done = 0
    skipped = 0
    for offset in range(0, len(items), BATCH):
        chunk = items[offset : offset + BATCH]
        entries = "".join(
            f'  set plan to plan & {{{{{item.row.index}, '
            f'"{_quote_as(item.row.persistent_id)}", '
            f'"{_quote_as(str(item.path))}"}}}}\n'
            for item in chunk
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
        set location of t to (POSIX file (item 3 of e))
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
            on_progress(min(offset + len(chunk), len(items)), len(items))
    return done, skipped


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = REPORTS / f"music-reconcile-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def _summary(plan: Plan) -> dict[str, Any]:
    reasons: dict[str, int] = {}
    for item in plan.relink:
        reasons[item.reason] = reasons.get(item.reason, 0) + 1
    return {
        "scanned": plan.scanned,
        "live": plan.live,
        "dead": len(plan.relink) + len(plan.duplicate) + len(plan.unresolved),
        "relink": len(plan.relink),
        "duplicate_rows": len(plan.duplicate),
        "unresolved": len(plan.unresolved),
        "by_reason": reasons,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ix_crate music-reconcile",
        description="Relink Music.app rows that lost their file.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="apply the relinks (default is a dry run)",
    )
    parser.add_argument(
        "--external",
        type=Path,
        default=None,
        help="backup Media.localized root to rebase unresolved rows onto",
    )
    parser.add_argument(
        "--external-scan",
        type=Path,
        default=None,
        help="wider external tree to artist/title match against",
    )
    parser.add_argument("--xml", type=Path, default=None, help="iTunes XML override")
    parser.add_argument(
        "--passes",
        type=int,
        default=6,
        help="max scan/relink rounds; rows regaining a file reorder the library "
        "and stale positions are skipped, so a few rounds are needed to converge",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    locations = xml_locations(args.xml)
    print(f"xml records {len(locations)} paths", flush=True)

    external_index = None
    if args.external_scan:
        print(f"index {args.external_scan}", flush=True)
        external_index = index_tree(args.external_scan.expanduser())

    def scanning(done: int, total: int) -> None:
        print(f"scan {done}/{total}", flush=True)

    def applying(done: int, total_items: int) -> None:
        print(f"relink {done}/{total_items}", flush=True)

    total_relinked = 0
    rounds = max(args.passes, 1) if args.execute else 1
    for round_no in range(1, rounds + 1):
        dead, claimed, total = scan_library(on_progress=scanning)
        print(f"live {len(claimed)}  dead {len(dead)}  of {total}", flush=True)

        plan = build_plan(
            dead,
            claimed,
            locations,
            external=args.external.expanduser() if args.external else None,
            external_index=external_index,
        )
        plan.scanned = total
        plan.live = len(claimed)

        summary = _summary(plan)
        for key, value in summary.items():
            print(f"{key}: {value}", flush=True)

        if not args.execute or not plan.relink:
            break

        print(f"pass {round_no}/{rounds}", flush=True)
        done, skipped = apply_relinks(plan.relink, on_progress=applying)
        total_relinked += done
        print(f"pass {round_no}: relinked {done}  skipped {skipped}", flush=True)
        if not done:
            break

    report = write_report(
        {
            **summary,
            "executed": bool(args.execute),
            "relink_plan": [
                {
                    "persistent_id": item.row.persistent_id,
                    "artist": item.row.artist,
                    "album": item.row.album,
                    "name": item.row.name,
                    "path": str(item.path),
                    "reason": item.reason,
                }
                for item in plan.relink
            ],
            "unresolved_rows": [
                {
                    "persistent_id": row.persistent_id,
                    "artist": row.artist,
                    "album": row.album,
                    "name": row.name,
                }
                for row in plan.unresolved
            ],
        }
    )
    print(f"report {report}", flush=True)

    if not args.execute:
        print("dry run, nothing changed. re-run with --execute", flush=True)
        return 0

    print(f"relinked {total_relinked} across {round_no} pass(es)", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
