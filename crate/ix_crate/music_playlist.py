"""Refill a Music.app playlist from download filenames + the library.

Matches Beatport ``123_Title_(Mix).mp3`` and ``Artist - Title.mp3`` against
existing Songs rows. Does not copy Downloads into Media.localized.
Does not add a second library row. Dry-run default.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from ix_crate.identify import (
    is_beatport_title,
    normalize_title,
    parse_filename,
    pretty_beatport_title,
    titles_match,
)
from ix_crate.music_dupes import MusicDupesError, _run_osascript, music_running
from ix_crate.music_fix import dump_playlist
from ix_crate.paths import APPLE_MUSIC, REPORTS, STEMS_AUDIO

DASH = re.compile(r"^(.+?)\s+-\s*(.+)$")
CONTRACTION_S = re.compile(r"\b(\w+)-s\b", re.I)
DEFAULT_PLAYLIST = "Never Forget 50th v01"


def _titles_ok(left: str, right: str) -> bool:
    if titles_match(left, right):
        return True
    return titles_match(left.replace("_", " "), right.replace("_", " "))


@dataclass
class Want:
    path: Path
    artist: str
    title: str


@dataclass
class Hit:
    persistent_id: str
    artist: str
    name: str
    location: str


@dataclass
class Match:
    want: Want
    hit: Hit | None
    reason: str


@dataclass
class PlaylistPlan:
    playlist: str
    sources: int = 0
    already: int = 0
    matched: int = 0
    missing: int = 0
    matches: list[Match] = field(default_factory=list)


def want_from_filename(path: Path) -> Want:
    stem = path.stem
    if is_beatport_title(stem):
        return Want(path=path, artist="", title=pretty_beatport_title(stem))
    match = DASH.match(stem)
    if match:
        title = CONTRACTION_S.sub(lambda m: m.group(1) + "'s", match.group(2).strip())
        return Want(path=path, artist=match.group(1).strip(), title=title)
    artist, _, title = parse_filename(stem)
    return Want(path=path, artist=artist, title=title or stem)


def collect_sources(root: Path) -> list[Path]:
    """MP3s in the folder plus one-level ``beatport_tracks_*`` children."""
    base = root.expanduser()
    found: list[Path] = []
    if not base.is_dir():
        return found
    for path in sorted(base.glob("*.mp3")):
        found.append(path)
    for folder in sorted(base.glob("beatport_tracks_*")):
        if folder.is_dir():
            found.extend(sorted(p for p in folder.glob("*.mp3") if p.is_file()))
    return found


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _score(hit: Hit, want: Want) -> tuple:
    loc = hit.location
    apple = str(APPLE_MUSIC)
    stems = str(STEMS_AUDIO)
    return (
        1 if loc.startswith(apple) else 0,
        1 if normalize_title(hit.name.replace("_", " ")) == normalize_title(want.title) else 0,
        1 if titles_match(hit.name, want.title) else 0,
        0 if loc.startswith(stems) else 1,
        len(hit.name),
    )


def search_library(want: Want) -> Hit | None:
    needle = want.title.split("(")[0].strip() or want.title
    if len(needle) < 3:
        needle = want.title
    needles = [needle]
    if "'" in needle:
        needles.append(needle.replace("'", "_"))
        needles.append(needle.replace("'", "\u2019"))
    candidates: list[Hit] = []
    seen: set[str] = set()
    for item in needles:
        quoted = _escape(item)
        script = f'''
tell application "Music"
  set hits to file tracks of library playlist 1 whose name contains "{quoted}"
  set out to ""
  repeat with t in hits
    set locText to ""
    try
      set locText to POSIX path of (location of t as alias)
    end try
    set out to out & (persistent ID of t as text) & tab & (artist of t as text) & tab & (name of t as text) & tab & locText & linefeed
  end repeat
  return out
end tell
'''
        text = _run_osascript(script, timeout=120)
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = (line.split("\t") + [""] * 4)[:4]
            pid, artist, name, location = (p.strip() for p in parts)
            if not pid or pid in seen:
                continue
            if not _titles_ok(name, want.title) and not _titles_ok(want.title, name):
                continue
            if want.artist and artist and not titles_match(artist.split(",")[0], want.artist.split(",")[0]):
                if normalize_title(want.artist) not in normalize_title(artist) and normalize_title(
                    artist
                ) not in normalize_title(want.artist):
                    continue
            seen.add(pid)
            candidates.append(Hit(persistent_id=pid, artist=artist, name=name, location=location))
        if candidates:
            break
    if not candidates:
        return None
    candidates.sort(key=lambda hit: _score(hit, want), reverse=True)
    return candidates[0]


def plan_playlist_fill(playlist: str, sources: list[Path]) -> PlaylistPlan:
    if not music_running():
        raise MusicDupesError("Music.app is not running. Open it and retry.")
    existing: set[str] = set()
    try:
        existing = {row.persistent_id for row in dump_playlist(playlist)}
    except MusicDupesError as exc:
        if "playlist not found" not in str(exc).lower():
            raise
    plan = PlaylistPlan(playlist=playlist, sources=len(sources), already=len(existing))
    seen: set[str] = set()
    for path in sources:
        want = want_from_filename(path)
        hit = search_library(want)
        if hit is None:
            plan.missing += 1
            plan.matches.append(Match(want=want, hit=None, reason="no library row"))
            continue
        if hit.persistent_id in seen:
            plan.matches.append(Match(want=want, hit=hit, reason="duplicate hit"))
            continue
        seen.add(hit.persistent_id)
        plan.matched += 1
        reason = "already in playlist" if hit.persistent_id in existing else "add"
        plan.matches.append(Match(want=want, hit=hit, reason=reason))
    return plan


def format_plan(plan: PlaylistPlan) -> str:
    lines = [
        f"music-playlist {plan.playlist!r}: {plan.sources} downloads  "
        f"library {plan.matched}  missing {plan.missing}  already {plan.already}"
    ]
    for item in plan.matches:
        title = item.want.title
        if item.hit is None:
            lines.append(f"  MISS  {title}  ({item.want.path.name})")
            continue
        loc = item.hit.location.replace(str(Path.home()), "~")
        lines.append(
            f"  {item.reason:18}  {item.hit.artist} — {item.hit.name}  {loc}"
        )
    return "\n".join(lines)


def apply_playlist(plan: PlaylistPlan) -> int:
    """Replace playlist contents with matched library rows. Files stay."""
    quoted = _escape(plan.playlist)
    pids = [item.hit.persistent_id for item in plan.matches if item.hit is not None]
    pid_list = ", ".join(f'"{pid}"' for pid in pids)
    script = f'''
tell application "Music"
  try
    set p to user playlist "{quoted}"
  on error
    set p to make new user playlist with properties {{name:"{quoted}"}}
  end try
  try
    delete (every track of p)
  end try
  set added to 0
  repeat with pid in {{{pid_list}}}
    set hits to file tracks of library playlist 1 whose persistent ID is pid
    if (count of hits) > 0 then
      duplicate (item 1 of hits) to p
      set added to added + 1
    end if
  end repeat
  return added as text
end tell
'''
    out = _run_osascript(script, timeout=300).strip()
    try:
        return int(out)
    except ValueError:
        return len(pids)


def write_report(plan: PlaylistPlan, extra: dict | None = None) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    payload = {
        "tool": "ix.crate.music-playlist",
        "playlist": plan.playlist,
        "sources": plan.sources,
        "matched": plan.matched,
        "missing": plan.missing,
        "already": plan.already,
        "hits": [
            {
                "file": str(item.want.path),
                "want_title": item.want.title,
                "want_artist": item.want.artist,
                "pid": item.hit.persistent_id if item.hit else "",
                "name": item.hit.name if item.hit else "",
                "artist": item.hit.artist if item.hit else "",
                "location": item.hit.location if item.hit else "",
                "reason": item.reason,
            }
            for item in plan.matches
        ],
        **(extra or {}),
    }
    dest = REPORTS / f"music-playlist-{stamp}.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--playlist",
        default=DEFAULT_PLAYLIST,
        help=f"Music.app user playlist (default {DEFAULT_PLAYLIST!r}).",
    )
    parser.add_argument(
        "--from",
        dest="source",
        type=Path,
        default=Path.home() / "Downloads",
        help="Folder of MP3s plus beatport_tracks_* (default ~/Downloads).",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    sources = collect_sources(args.source)
    if not sources:
        print(f"no mp3s in {args.source}", flush=True)
        return 2
    plan = plan_playlist_fill(args.playlist, sources)
    print(format_plan(plan), flush=True)
    report = write_report(plan, {"execute": args.execute})
    print(f"report: {report}", flush=True)
    if not args.execute:
        print(
            "dry-run. pass --execute to replace the playlist with matched library rows. "
            "Downloads stay. No Media.localized copies.",
            flush=True,
        )
        return 0
    added = apply_playlist(plan)
    print(f"playlist now {added} tracks. Open Music.app and check {args.playlist!r}.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
