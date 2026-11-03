"""phone-status — BABYLON / STEMIT progress as a tiny JSON on your own iCloud Drive.

The iPhone widget (``docs/examples/iphone/babylon-widget.js``, Scriptable)
reads it. No listener on the Mac and no third-party service: the file rides
the signed-in Apple ID's iCloud Drive, so only that account sees it. Track
names only, never disk paths.

BABYLON writes it in-process (attached or detached). For a run started
elsewhere, tail its log:

    PYTHONPATH=crate python3 -m ix_crate phone-status --log <babylon-….log> --pid <babylon pid>

Folder: ``$IX_STATUS_DIR``, else Scriptable's iCloud folder (``…/ix``) once
Scriptable has synced on the phone, else ``iCloud Drive/ix``. ``IX_PHONE_STATUS=0``
turns it off.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_NAME = "babylon-status.json"
MOBILE_DOCS = Path.home() / "Library" / "Mobile Documents"
SCRIPTABLE_DOCS = MOBILE_DOCS / "iCloud~dk~simonbs~Scriptable" / "Documents"
ICLOUD_DRIVE = MOBILE_DOCS / "com~apple~CloudDocs"
WRITE_EVERY_S = 15.0

PHASE = re.compile(r"^=== phase (?:(\d+)/(\d+): )?(.+?) ===$")
PASS = re.compile(r"^(ok|fail) (\d+)/(\d+)\b\s*(.*)")
FILE = re.compile(r"Processing file: (.+)$")
STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
CHUNKS = re.compile(r"Processing audio chunks:\s+(\d+)%")
SCAN = re.compile(r"^(?:scan|library|dump) (\d+)/(\d+)", re.I)
QUEUED = re.compile(r"^queued (\d+) across")
PLAN_GENRE = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:]+Z (.+?): \d+ tracks\s+\d+ to stem")


def utc_iso(ts: float | None = None) -> str:
    stamp = datetime.fromtimestamp(ts if ts is not None else time.time(), timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _line_time(line: str) -> float | None:
    """Separator log lines start with local wall time."""
    m = STAMP.match(line)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def status_dir() -> Path | None:
    raw = os.environ.get("IX_STATUS_DIR", "").strip()
    if raw:
        return Path(raw).expanduser()
    if SCRIPTABLE_DOCS.is_dir():
        return SCRIPTABLE_DOCS / "ix"
    if ICLOUD_DRIVE.is_dir():
        return ICLOUD_DRIVE / "ix"
    return None


def enabled() -> bool:
    return os.environ.get("IX_PHONE_STATUS", "1").strip() not in {"0", "false", "no", "off"}


class PhoneStatus:
    """Parse progress lines; write ``babylon-status.json`` at most every 15 s."""

    def __init__(self, title: str, out: Path, *, started: float | None = None) -> None:
        self.title = title
        self.out = out
        self.started = started if started is not None else time.time()
        self.state = "running"
        self.phase_index = 0
        self.phase_total = 0
        self.phase_name = ""
        self.step = ""
        self.passes_done = 0
        self.passes_total = 0
        self.passes_failed = 0
        self.last_fail = ""
        self.track = ""
        self.track_pct: int | None = None
        self.queued = 0
        self.stem_started: float | None = None
        self.summary = ""
        self._last_write = 0.0
        self._dirty = True

    @classmethod
    def open(cls, title: str, *, started: float | None = None) -> PhoneStatus | None:
        if not enabled():
            return None
        folder = status_dir()
        if folder is None:
            return None
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
        status = cls(title, folder / STATUS_NAME, started=started)
        status.flush(force=True)
        return status

    def phase(self, index: int, total: int, name: str) -> None:
        self.phase_index, self.phase_total, self.phase_name = index, total, name
        self.step = ""
        self.track_pct = None
        self._dirty = True
        self.flush(force=True)

    def feed(self, text: str, *, now: float | None = None) -> None:
        for raw in re.split(r"[\r\n]+", text):
            line = raw.strip()
            if line:
                self._line(line, now if now is not None else time.time())
        self.flush(now=now)

    def _line(self, line: str, now: float) -> None:
        m = PHASE.match(line)
        if m:
            if m.group(1):
                self.phase_index, self.phase_total = int(m.group(1)), int(m.group(2))
            self.phase_name = m.group(3)
            self.step, self.track_pct = "", None
            self._dirty = True
            return
        m = PASS.match(line)
        if m:
            kind, done, total, rest = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            if self.stem_started is None:
                self.stem_started = now
            self.passes_done, self.passes_total = done, total
            if kind == "fail":
                self.passes_failed += 1
                self.last_fail = rest.split(":", 1)[0].strip()
            self.track_pct = None
            self._dirty = True
            return
        m = FILE.search(line)
        if m:
            self.track = Path(m.group(1).strip()).stem
            self.track_pct = 0
            if self.stem_started is None:
                self.stem_started = _line_time(line) or now
            self._dirty = True
            return
        m = CHUNKS.search(line)
        if m:
            self.track_pct = int(m.group(1))
            self._dirty = True
            return
        m = QUEUED.match(line)
        if m:
            self.queued = int(m.group(1))
            self._dirty = True
            return
        m = PLAN_GENRE.match(line)
        if m:
            self.step = f"planning {m.group(1)}"
            self._dirty = True
            return
        m = SCAN.match(line)
        if m:
            self.step = f"{m.group(0).split()[0]} {m.group(1)}/{m.group(2)}"
            self._dirty = True
            return
        if line.startswith("CRATER "):
            self.step = line[:80]
            self._dirty = True
            return
        if line.startswith("Traceback"):
            self.step = f"error in {self.phase_name}" if self.phase_name else "error"
            self._dirty = True

    def eta_min(self, now: float) -> float | None:
        if self.stem_started is None or self.passes_done <= 0 or not self.passes_total:
            return None
        remaining = max(self.passes_total - self.passes_done, 0)
        rate = (now - self.stem_started) / self.passes_done
        return round(rate * remaining / 60, 1)

    def payload(self, now: float | None = None) -> dict[str, Any]:
        now = now if now is not None else time.time()
        return {
            "title": self.title,
            "state": self.state,
            "updated_at": utc_iso(now),
            "started_at": utc_iso(self.started),
            "elapsed_min": round((now - self.started) / 60, 1),
            "phase": {"index": self.phase_index, "total": self.phase_total, "name": self.phase_name},
            "step": self.step,
            "passes": {
                "done": self.passes_done,
                "total": self.passes_total,
                "failed": self.passes_failed,
                "queued_tracks": self.queued,
            },
            "track": self.track,
            "track_pct": self.track_pct,
            "eta_min": self.eta_min(now),
            "last_fail": self.last_fail,
            "summary": self.summary,
        }

    def flush(self, *, force: bool = False, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        if not force and (not self._dirty or now - self._last_write < WRITE_EVERY_S):
            return
        tmp = self.out.with_name(f".{self.out.name}.tmp")
        try:
            tmp.write_text(json.dumps(self.payload(now), indent=1) + "\n", encoding="utf-8")
            os.replace(tmp, self.out)
        except OSError:
            return
        self._last_write = now
        self._dirty = False

    def finish(self, state: str, summary: str = "") -> None:
        self.state = state
        self.summary = summary
        self.track_pct = None
        self.flush(force=True)


def _log_started(log: Path) -> float:
    m = re.search(r"(\d{8}T\d{6}Z)", log.name)
    if m:
        stamp = datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return stamp.timestamp()
    return log.stat().st_mtime


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def tail(log: Path, *, pid: int | None, title: str) -> int:
    status = PhoneStatus.open(title, started=_log_started(log))
    if status is None:
        print("phone-status off (IX_PHONE_STATUS=0 or no iCloud Drive)", file=sys.stderr)
        return 2
    print(f"phone status: {status.out}", flush=True)
    offset = 0
    done = False
    first = True
    while True:
        try:
            size = log.stat().st_size
        except OSError:
            size = offset
        if size > offset:
            with log.open("rb") as handle:
                handle.seek(offset)
                chunk = handle.read(size - offset)
            offset = size
            text = chunk.decode("utf-8", errors="replace")
            status.feed(text)
            if first:
                status.flush(force=True)
                first = False
            if "CRATER done." in text or "run json (copy):" in text:
                done = True
        else:
            status._dirty = True
            status.flush()
        if pid is not None and not _alive(pid):
            break
        if pid is None and done:
            break
        time.sleep(5)
    if done:
        status.finish("done", "CRATER done")
    else:
        status.finish("stopped", f"stopped in {status.phase_name}" if status.phase_name else "stopped")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ix_crate phone-status", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, required=True, help="BABYLON / STEMIT log to tail.")
    parser.add_argument("--pid", type=int, default=None, help="Stop when this process exits.")
    parser.add_argument("--title", default="BABYLON")
    args = parser.parse_args(argv)
    return tail(args.log.expanduser(), pid=args.pid, title=args.title)


if __name__ == "__main__":
    raise SystemExit(main())
