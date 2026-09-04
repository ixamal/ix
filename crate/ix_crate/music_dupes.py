"""Find Music.app library rows that share one file on disk, and drop extras.

Same POSIX location, two (or more) Songs rows — Show in Finder opens the
same file. This removes the extra *library entries* only. It never unlinks
audio, never writes Media.localized, and never touches .stem.m4a tags.

Dry-run is the default. --execute deletes leftover rows via AppleScript.
After each delete the file must still exist; if Music moved it to Trash
we put it back and stop.

Keep the row with more playlist hits, then plays, then rating, then the
oldest database id. Cloud rows with no location are ignored.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ix_crate.paths import REPORTS
from ix_crate.stems_path import ensure_stems_path

BATCH = 200
HUD_TITLE = "Music library dupes"
TOOL_ID = "ix.crate.music_dupes"


class MusicDupesError(RuntimeError):
    pass


@dataclass
class TrackRow:
    persistent_id: str
    database_id: int
    artist: str
    album: str
    name: str
    location: str
    played_count: int
    rating: int
    playlist_hits: int = 0


@dataclass
class DupeGroup:
    location: str
    keep: TrackRow
    extras: list[TrackRow] = field(default_factory=list)

    @property
    def size(self) -> int:
        return 1 + len(self.extras)


def canon_path(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    path = Path(text)
    try:
        if path.is_file():
            return str(path.resolve())
    except OSError:
        pass
    return str(path)


def keep_key(row: TrackRow) -> tuple[int, int, int, int]:
    return (row.playlist_hits, row.played_count, row.rating, -row.database_id)


def pick_keeper(rows: list[TrackRow]) -> TrackRow:
    if not rows:
        raise ValueError("empty group")
    ordered = sorted(rows, key=lambda row: row.database_id)
    return max(ordered, key=keep_key)


def group_file_rows(rows: Iterable[TrackRow]) -> list[DupeGroup]:
    buckets: dict[str, list[TrackRow]] = defaultdict(list)
    for row in rows:
        key = canon_path(row.location)
        if not key:
            continue
        if not Path(key).is_file():
            continue
        buckets[key].append(row)
    groups: list[DupeGroup] = []
    for location, members in sorted(buckets.items()):
        if len(members) < 2:
            continue
        keep = pick_keeper(members)
        extras = [row for row in members if row.persistent_id != keep.persistent_id]
        extras.sort(key=lambda row: (row.database_id, row.persistent_id))
        groups.append(DupeGroup(location=location, keep=keep, extras=extras))
    return groups


def _run_osascript(script: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["osascript"],
        input=script,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "osascript failed").strip()
        raise MusicDupesError(err)
    return result.stdout


def music_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-f", "/System/Applications/Music.app/Contents/MacOS/Music"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def count_file_tracks() -> int:
    out = _run_osascript(
        'tell application "Music" to count file tracks of library playlist 1'
    )
    return int(out.strip() or "0")


def count_user_playlists() -> int:
    out = _run_osascript('tell application "Music" to count user playlists')
    return int(out.strip() or "0")


def _clean_field(value: str) -> str:
    return value.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def _parse_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value.strip()))
    except ValueError:
        return default


def dump_file_track_batch(start: int, end: int) -> list[TrackRow]:
    """1-based inclusive file-track range → rows. Location may be empty."""
    script = f'''
tell application "Music"
  set pids to (persistent ID of file tracks {start} thru {end} of library playlist 1) as list
  set dbids to (database ID of file tracks {start} thru {end} of library playlist 1) as list
  set nms to (name of file tracks {start} thru {end} of library playlist 1) as list
  set ars to (artist of file tracks {start} thru {end} of library playlist 1) as list
  set als to (album of file tracks {start} thru {end} of library playlist 1) as list
  set pcs to (played count of file tracks {start} thru {end} of library playlist 1) as list
  set rts to (rating of file tracks {start} thru {end} of library playlist 1) as list
  set locs to (location of file tracks {start} thru {end} of library playlist 1) as list
  set out to ""
  repeat with i from 1 to count of pids
    set locText to ""
    try
      set locText to POSIX path of (item i of locs)
    end try
    set out to out & (item i of pids as text) & tab & (item i of dbids as text) & tab & (item i of ars as text) & tab & (item i of als as text) & tab & (item i of nms as text) & tab & (item i of pcs as text) & tab & (item i of rts as text) & tab & locText & linefeed
  end repeat
  return out
end tell
'''
    text = _run_osascript(script, timeout=180)
    rows: list[TrackRow] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 8:
            parts = parts + [""] * (8 - len(parts))
        pid, dbid, artist, album, name, plays, rating, location = parts[:8]
        if not pid.strip():
            continue
        rows.append(
            TrackRow(
                persistent_id=pid.strip(),
                database_id=_parse_int(dbid),
                artist=_clean_field(artist),
                album=_clean_field(album),
                name=_clean_field(name),
                location=location.strip(),
                played_count=_parse_int(plays),
                rating=_parse_int(rating),
            )
        )
    return rows


def dump_playlist_persistent_ids(index: int) -> list[str]:
    script = f'''
tell application "Music"
  try
    set p to user playlist {index}
    if class of p is folder playlist then return ""
    try
      if smart of p is true then return ""
    end try
    set pids to persistent ID of file tracks of p
    set AppleScript's text item delimiters to linefeed
    return pids as text
  on error
    return ""
  end try
end tell
'''
    text = _run_osascript(script, timeout=60)
    return [line.strip() for line in text.splitlines() if line.strip()]


def apply_playlist_hits(rows: list[TrackRow], wanted: set[str], on_step=None) -> None:
    if not wanted:
        return
    counts = {pid: 0 for pid in wanted}
    n = count_user_playlists()
    for index in range(1, n + 1):
        if on_step:
            on_step(index, n)
        for pid in dump_playlist_persistent_ids(index):
            if pid in counts:
                counts[pid] += 1
    for row in rows:
        row.playlist_hits = counts.get(row.persistent_id, 0)


def scan_library(on_scan=None, on_playlists=None) -> tuple[list[TrackRow], int]:
    if not music_running():
        raise MusicDupesError("Music.app is not running. Open it and retry.")
    total = count_file_tracks()
    rows: list[TrackRow] = []
    start = 1
    while start <= total:
        end = min(start + BATCH - 1, total)
        if on_scan:
            on_scan(end, total)
        rows.extend(dump_file_track_batch(start, end))
        start = end + 1
    if on_playlists:
        located = [row for row in rows if row.persistent_id]
        apply_playlist_hits(located, {row.persistent_id for row in located}, on_step=on_playlists)
    return rows, total


def delete_library_row(persistent_id: str) -> None:
    if not persistent_id.isalnum() or len(persistent_id) > 32:
        raise MusicDupesError(f"refusing persistent id {persistent_id!r}")
    script = f'''
tell application "Music"
  set hits to file tracks of library playlist 1 whose persistent ID is "{persistent_id}"
  if (count of hits) is not 1 then
    error "expected 1 track for {persistent_id}, got " & (count of hits)
  end if
  delete item 1 of hits
end tell
'''
    _run_osascript(script, timeout=45)


def restore_from_trash(path: Path) -> bool:
    script = f'''
tell application "Finder"
  set hits to every item of trash whose name is "{path.name.replace('"', "")}"
  if (count of hits) is 0 then return "none"
  put away item 1 of hits
  return "ok"
end tell
'''
    try:
        out = _run_osascript(script, timeout=30).strip()
    except MusicDupesError:
        return False
    return out == "ok" and path.is_file()


def delete_extra_row(row: TrackRow) -> dict[str, Any]:
    path = Path(canon_path(row.location) or row.location)
    existed = path.is_file()
    delete_library_row(row.persistent_id)
    if existed and not path.is_file():
        restored = restore_from_trash(path)
        raise MusicDupesError(
            "Music.app removed the audio after deleting a library row. "
            f"{'Restored from Trash. ' if restored else 'Could not restore. '}"
            f"Stopped. path={path}"
        )
    return {"persistent_id": row.persistent_id, "kept_file": str(path)}


def write_report(payload: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = REPORTS / f"music-dupes-{stamp}.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def groups_payload(groups: list[DupeGroup], scanned: int, file_tracks: int) -> dict[str, Any]:
    extras = sum(len(group.extras) for group in groups)
    return {
        "scanned_rows": scanned,
        "file_tracks": file_tracks,
        "dupe_files": len(groups),
        "extra_rows": extras,
        "groups": [
            {
                "location": group.location,
                "count": group.size,
                "keep": asdict(group.keep),
                "extras": [asdict(row) for row in group.extras],
            }
            for group in groups
        ],
    }


def print_groups(groups: list[DupeGroup], *, limit: int = 30) -> None:
    extras = sum(len(group.extras) for group in groups)
    print(
        f"{len(groups)} files with extra Music.app rows; {extras} rows to drop",
        flush=True,
    )
    for group in groups[:limit]:
        keep = group.keep
        print(
            f"  KEEP {keep.persistent_id}  playlists={keep.playlist_hits} "
            f"plays={keep.played_count}  {keep.artist} — {keep.name}",
            flush=True,
        )
        for row in group.extras:
            print(
                f"    drop {row.persistent_id}  playlists={row.playlist_hits} "
                f"plays={row.played_count}  {row.artist} — {row.name}",
                flush=True,
            )
        print(f"    file {group.location}", flush=True)
    if len(groups) > limit:
        print(f"  … {len(groups) - limit} more files", flush=True)


class MusicDupes:
    """Scan + optional library-row delete. Dry-run by default."""

    run_log: Any = None

    def __init__(self, *, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.groups: list[DupeGroup] = []
        self.report_path: Path | None = None

    def _panel(self):
        logger = getattr(self, "run_log", None)
        return getattr(logger, "panel", None) if logger is not None else None

    def _hud(self, index: int, total: int, name: str, action: str) -> None:
        panel = self._panel()
        if panel is None:
            return
        try:
            panel.set_totals(max(total, 1), max(total, 1))
            panel.set_job(index, max(total, 1), name, action)
        except Exception:
            pass

    def plan(self) -> list:
        ensure_stems_path()
        from py.utils.base import Job

        def on_scan(done: int, total: int) -> None:
            print(f"scan {done}/{total} file tracks", flush=True)
            self._hud(done, total, "library", "scan")

        def on_playlists(done: int, total: int) -> None:
            print(f"playlists {done}/{total}", flush=True)
            self._hud(done, total, "user playlists", "playlists")

        rows, file_tracks = scan_library(on_scan=on_scan, on_playlists=None)
        preliminary = group_file_rows(rows)
        wanted = {
            row.persistent_id
            for group in preliminary
            for row in (group.keep, *group.extras)
        }
        if wanted:
            apply_playlist_hits(rows, wanted, on_step=on_playlists)
        self.groups = group_file_rows(rows)
        payload = groups_payload(self.groups, scanned=len(rows), file_tracks=file_tracks)
        self.report_path = write_report(payload)
        print_groups(self.groups)
        print(f"report: {self.report_path}", flush=True)

        jobs = []
        for group in self.groups:
            source = Path(group.location)
            for extra in group.extras:
                jobs.append(
                    Job(
                        source,
                        source,
                        "delete-row" if not self.dry_run else "drop-row",
                        f"keep {group.keep.persistent_id}",
                        extra={
                            "persistent_id": extra.persistent_id,
                            "keep_id": group.keep.persistent_id,
                            "artist": extra.artist,
                            "name": extra.name,
                        },
                    )
                )
        return jobs

    def print_plan(self, jobs: list) -> None:
        mode = "dry-run" if self.dry_run else "execute"
        print(
            f"{mode}: {len(jobs)} extra library rows / {len(self.groups)} files",
            flush=True,
        )
        if self.dry_run:
            print("dry-run. pass --execute to delete extra Music.app rows (file stays).", flush=True)

    def run(self) -> list:
        ensure_stems_path()
        from py.utils.base import Job

        jobs = self.plan()
        self.print_plan(jobs)
        logger = getattr(self, "run_log", None)
        if logger is not None and hasattr(logger, "execute_logged"):
            pass

        def apply(job: Job) -> dict[str, Any]:
            pid = str(job.extra.get("persistent_id") or "")
            row = TrackRow(
                persistent_id=pid,
                database_id=0,
                artist=str(job.extra.get("artist") or ""),
                album="",
                name=str(job.extra.get("name") or job.source.name),
                location=str(job.source),
                played_count=0,
                rating=0,
            )
            return delete_extra_row(row)

        if logger is not None:
            from py.utils.runlog import execute_logged

            return execute_logged(self, jobs, None if self.dry_run else apply)
        if self.dry_run:
            return jobs
        for job in jobs:
            apply(job)
            print(f"ok delete-row {job.extra.get('persistent_id')} {job.source.name}", flush=True)
        return jobs


def run_with_hud(args: argparse.Namespace, tool: MusicDupes) -> int:
    ensure_stems_path()
    from py.utils.notify import notify_complete, resolve_charts, summary_from_payload
    from py.utils.progress import ProgressPanel
    from py.utils.runlog import RunLogger, is_verbose, want_notify

    want_panel = True if getattr(args, "gui", None) is None else bool(args.gui)
    panel = ProgressPanel.try_open(HUD_TITLE) if want_panel else None
    logger = RunLogger(
        TOOL_ID,
        verbose=is_verbose(args),
        dry_run=tool.dry_run,
        panel=panel,
    )
    tool.run_log = logger

    def work() -> None:
        try:
            tool.run()
        except Exception as exc:
            print(f"run failed: {exc}", flush=True)
        finally:
            try:
                logger.close()
            except Exception as exc:
                print(f"run log close failed: {exc}", flush=True)
            payload = logger.payload or {}
            summary = summary_from_payload(payload) if payload else f"{TOOL_ID} finished"
            if tool.report_path:
                summary = f"{summary}  report {tool.report_path.name}"
            charts = resolve_charts(payload)
            if want_notify(args, tool.dry_run):
                notify_complete(title=HUD_TITLE, body=summary, payload=payload)
            if panel is not None:
                try:
                    panel.finish(summary, charts=charts)
                except Exception as exc:
                    print(f"progress GUI finish skipped ({exc})", flush=True)

    if panel is None:
        work()
        return 0
    worker = threading.Thread(target=work, name="music-dupes", daemon=False)
    worker.start()
    panel.mainloop()
    worker.join()
    return 0


def build_parser() -> argparse.ArgumentParser:
    ensure_stems_path()
    from py.utils.runlog import add_log_flags

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Delete extra Music.app rows. File on disk stays. Default is dry-run.",
    )
    add_log_flags(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "gui", None) is None:
        args.gui = True
    tool = MusicDupes(dry_run=not args.execute)
    try:
        return run_with_hud(args, tool)
    except MusicDupesError as exc:
        print(exc, file=sys.stderr)
        return 2
