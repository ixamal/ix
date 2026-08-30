"""Dry-run move plans. Families stay together. Default is no writes."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ix_crate.families import discover_families
from ix_crate.identify import Identity, is_placeholder_album_folder
from ix_crate.lookup import resolve
from ix_crate.mashup import identify_mashup
from ix_crate.paths import (
    OUTLIERS_INBOX,
    REPORTS,
    STEMS_AUDIO,
    UNKNOWN_ALBUM,
    UNKNOWN_MASHUPS,
)
from ix_crate.safety import CrateSafetyError, assert_under_stems


@dataclass
class Move:
    src: str
    dest: str
    family: str
    artist: str
    album: str
    title: str
    source: str
    action: str


def plan_family(
    family, root: Path, used: set[str], *, lookup: bool
) -> tuple[Identity, list[Move]]:
    identity = resolve(family, lookup=lookup)
    dest_dir = root / identity.dest_artist / identity.dest_album
    moves: list[Move] = []
    for path in family.files:
        dest = dest_dir / path.name
        key = str(dest).lower()
        try:
            same = dest.exists() and dest.resolve() == path.resolve()
        except OSError:
            same = False
        if same:
            action = "already"
        elif dest.exists() or key in used:
            action = "skip-collision"
        else:
            action = "move"
            used.add(key)
        moves.append(
            Move(
                src=str(path),
                dest=str(dest),
                family=family.key,
                artist=identity.dest_artist,
                album=identity.dest_album,
                title=identity.title,
                source=identity.source,
                action=action,
            )
        )
    return identity, moves


def plan_scan(
    scan: Path,
    root: Path | None = None,
    *,
    lookup: bool = True,
    kind: str,
) -> dict:
    stems = assert_under_stems(root or STEMS_AUDIO)
    folder = assert_under_stems(scan)
    if not folder.is_dir():
        raise CrateSafetyError(f"Missing {folder}")
    used: set[str] = set()
    all_moves: list[Move] = []
    sources: Counter[str] = Counter()
    families = discover_families(folder)
    for index, family in enumerate(families, start=1):
        print(f"[{index}/{len(families)}] {family.key[:90]}", flush=True)
        identity, moves = plan_family(family, stems, used, lookup=lookup)
        all_moves.extend(moves)
        sources[identity.source] += 1
    dest_unknown = [
        move.dest for move in all_moves if "unknown" in move.dest.lower()
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "root": str(stems),
        "scan": str(folder),
        "lookup": lookup,
        "families": len(families),
        "files": len(all_moves),
        "sources": dict(sources),
        "outliers": sources.get("outlier", 0),
        "unknown_in_dest": dest_unknown,
        "moves": [asdict(item) for item in all_moves],
    }


def plan_unknown_album(root: Path | None = None, *, lookup: bool = True) -> dict:
    return plan_scan(UNKNOWN_ALBUM, root, lookup=lookup, kind="unknown-album")


def plan_outliers(root: Path | None = None, *, lookup: bool = True) -> dict:
    return plan_scan(OUTLIERS_INBOX, root, lookup=lookup, kind="outliers")


def _mashup_family_moves(
    family,
    stems: Path,
    used: set[str],
    identity: Identity,
) -> list[Move]:
    dest_dir = stems / identity.dest_artist / identity.dest_album
    rebuilt: list[Move] = []
    for path in family.files:
        dest = dest_dir / path.name
        key = str(dest).lower()
        try:
            same = dest.exists() and dest.resolve() == path.resolve()
        except OSError:
            same = False
        if same:
            action = "already"
        elif dest.exists() or key in used:
            action = "skip-collision"
        else:
            action = "move"
            used.add(key)
        rebuilt.append(
            Move(
                src=str(path),
                dest=str(dest),
                family=family.key,
                artist=identity.artist,
                album=identity.dest_album,
                title=identity.title,
                source="mashup",
                action=action,
            )
        )
    return rebuilt


def iter_unknown_albums(root: Path) -> list[Path]:
    found: list[Path] = []
    compilations = root / "Compilations"
    outliers = root / "_outliers"
    for folder in sorted(p for p in root.rglob("*") if p.is_dir()):
        if folder == root or folder.parent == root:
            continue
        if not is_placeholder_album_folder(folder.name):
            continue
        try:
            folder.relative_to(compilations)
            continue
        except ValueError:
            pass
        try:
            folder.relative_to(outliers)
            continue
        except ValueError:
            pass
        found.append(folder)
    return found


def iter_mashup_albums(root: Path) -> list[Path]:
    found: list[Path] = []
    compilations = root / "Compilations"
    for folder in sorted(root.rglob("Mashups")):
        if not folder.is_dir():
            continue
        if folder.parent == root:
            continue
        try:
            folder.relative_to(compilations)
            continue
        except ValueError:
            found.append(folder)
    return found


def plan_mashups(root: Path | None = None, *, lookup: bool = False) -> dict:
    """Inbox + every Unknown Album mashup family → Compilations/Mashups/{Artist}/."""
    del lookup
    stems = assert_under_stems(root or STEMS_AUDIO)
    used: set[str] = set()
    all_moves: list[Move] = []
    sources: Counter[str] = Counter()
    family_count = 0
    scans: list[str] = []

    targets: list[tuple[Path, bool, str]] = []
    if OUTLIERS_INBOX.is_dir():
        targets.append((OUTLIERS_INBOX, False, ""))
    if UNKNOWN_MASHUPS.is_dir():
        targets.append((UNKNOWN_MASHUPS, True, ""))
    for folder in iter_unknown_albums(stems):
        targets.append((folder, True, folder.parent.name))
    for folder in iter_mashup_albums(stems):
        targets.append((folder, True, folder.parent.name))

    for folder, force, parent in targets:
        scans.append(str(folder))
        families = discover_families(assert_under_stems(folder))
        for family in families:
            identity = identify_mashup(family, force=force, parent=parent)
            if identity is None:
                continue
            family_count += 1
            print(f"[{family_count}] {family.key[:90]} → {identity.artist}", flush=True)
            all_moves.extend(_mashup_family_moves(family, stems, used, identity))
            sources["mashup"] += 1
    dest_unknown = [
        move.dest for move in all_moves if "unknown" in move.dest.lower()
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "mashups",
        "root": str(stems),
        "scan": scans,
        "lookup": False,
        "families": family_count,
        "files": len(all_moves),
        "sources": dict(sources),
        "outliers": 0,
        "unknown_in_dest": dest_unknown,
        "moves": [asdict(item) for item in all_moves],
    }


def write_report(payload: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    kind = str(payload.get("kind") or "scan")
    path = REPORTS / f"{kind}-{stamp}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def execute_moves(payload: dict) -> int:
    moved = 0
    for item in payload["moves"]:
        if item["action"] != "move":
            continue
        src = assert_under_stems(Path(item["src"]))
        dest = assert_under_stems(Path(item["dest"]))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        moved += 1
    return moved
