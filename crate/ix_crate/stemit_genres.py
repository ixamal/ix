"""STEMIT genre crates from cleaned NML / file tags.

Rebuilds ``STEMIT/Genres/<Genre>/{Mixes,Stems,Acapellas,Instrumentals}``
from the same disk keepers as the four root STEMIT crates. Safe to re-run
when stems are added or copies dropped.

Cleans ``EDM, …`` and ``House, …`` with ``music_genre.clean_genre``.
Patches Traktor INFO GENRE only when NML is rebuilt. Never mutagen-writes
``.wav`` / ``.stem.m4a``. Never writes Apple Music. Rekordbox STEMIT /
Genres crates are written to ``rekordbox.xml`` from the current NML.
"""

from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ix_crate.families import family_key
from ix_crate.identify import normalize_title
from ix_crate.music_genre import clean_genre
from ix_crate.music_repair import RIFF_NO_ID3, SKIP_SUFFIX
from ix_crate.paths import REPORTS
from ix_crate.stems_playlists import (
    FOLDER_NAME,
    PLAYLISTS,
    TRAKTOR_NML,
    DiskFile,
    _ensure_traktor_folder,
    _ensure_traktor_playlist,
    _loc_to_path,
    classify,
    prefer_crate_files,
    walk_stems,
)
from ix_crate.traktor_nml import is_stem_container

UNTAGGED = "Untagged"
GENRES_FOLDER = "Genres"
TAGGABLE = {".mp3", ".m4a"}


def _append_folder(parent, name: str):
    """Folder as last child. ``_ensure_traktor_folder`` inserts at 0."""
    subnodes = parent.find("SUBNODES")
    if subnodes is None:
        subnodes = ET.SubElement(parent, "SUBNODES", COUNT="0")
    for node in subnodes.findall("NODE"):
        if node.get("TYPE") == "FOLDER" and node.get("NAME") == name:
            kids = node.find("SUBNODES")
            if kids is None:
                kids = ET.SubElement(node, "SUBNODES", COUNT="0")
            return node
    folder = ET.Element("NODE", TYPE="FOLDER", NAME=name)
    ET.SubElement(folder, "SUBNODES", COUNT="0")
    subnodes.append(folder)
    subnodes.set("COUNT", str(len(list(subnodes))))
    return folder


@dataclass
class GenreHit:
    path: str
    crate: str
    old: str
    new: str
    source: str


@dataclass
class GenreCratePlan:
    files: int = 0
    patched: int = 0
    by_genre: dict[str, int] = field(default_factory=dict)
    by_source: dict[str, int] = field(default_factory=dict)
    hits: list[GenreHit] = field(default_factory=list)


def read_file_genre(path: Path) -> str:
    """Genre tag on owned mp3/m4a. Never opens wav or stem containers."""
    if not path.is_file():
        return ""
    if is_stem_container(path):
        return ""
    suffix = path.suffix.lower()
    if suffix not in TAGGABLE or suffix in RIFF_NO_ID3:
        return ""
    if any(path.name.lower().endswith(skip) for skip in SKIP_SUFFIX):
        return ""
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path, easy=True)
    except Exception:
        return ""
    if audio is None or audio.tags is None:
        return ""
    values = audio.tags.get("genre")
    return str(values[0]).strip() if values else ""


def sibling_mix_genre(path: Path) -> str:
    parent = path.parent
    if not parent.is_dir():
        return ""
    want = normalize_title(family_key(path))
    if not want:
        return ""
    for item in parent.iterdir():
        if not item.is_file() or classify(item) != "Mixes":
            continue
        if normalize_title(family_key(item)) != want:
            continue
        genre = read_file_genre(item)
        if genre:
            return genre
    return ""


def nml_genre(entry) -> str:
    info = entry.find("INFO")
    if info is None:
        return ""
    return (info.get("GENRE") or "").strip()


def set_nml_genre(entry, genre: str) -> None:
    info = entry.find("INFO")
    if info is None:
        info = ET.SubElement(entry, "INFO")
    info.set("GENRE", genre)


def collection_by_path(collection, stems_root: Path) -> dict[Path, object]:
    found: dict[Path, object] = {}
    base = stems_root.expanduser().resolve()
    for entry in collection.findall("ENTRY"):
        location = entry.find("LOCATION")
        if location is None:
            continue
        directory = location.get("DIR") or ""
        if "stems_audio" not in directory:
            continue
        path = _loc_to_path(directory, location.get("FILE") or "")
        try:
            path.relative_to(base)
        except ValueError:
            continue
        found[path.resolve()] = entry
    return found


def resolve_genre(path: Path, entry=None) -> tuple[str, str]:
    """Return (cleaned genre or Untagged, source)."""
    if entry is not None:
        tagged = nml_genre(entry)
        if tagged:
            cleaned = clean_genre(tagged) or UNTAGGED
            return cleaned, "nml"
    tagged = read_file_genre(path)
    if tagged:
        return clean_genre(tagged) or UNTAGGED, "file"
    tagged = sibling_mix_genre(path)
    if tagged:
        return clean_genre(tagged) or UNTAGGED, "sibling-mix"
    return UNTAGGED, "untagged"


def plan_genre_crates(
    *,
    stems_root: Path | None = None,
    nml: Path | None = None,
    files: list[DiskFile] | None = None,
) -> tuple[GenreCratePlan, list[DiskFile], dict[Path, str]]:
    from ix_crate.paths import STEMS_AUDIO

    root = (stems_root or STEMS_AUDIO).expanduser()
    nml_path = nml or TRAKTOR_NML
    keepers = files if files is not None else prefer_crate_files(walk_stems(root), root)
    plan = GenreCratePlan(files=len(keepers))
    assigned: dict[Path, str] = {}
    entries: dict[Path, object] = {}
    if nml_path.is_file():
        import xml.etree.ElementTree as ET

        collection = ET.parse(nml_path).getroot().find("COLLECTION")
        if collection is not None:
            entries = collection_by_path(collection, root)
    for item in keepers:
        path = item.path.resolve()
        entry = entries.get(path)
        genre, source = resolve_genre(path, entry)
        old = nml_genre(entry) if entry is not None else ""
        assigned[path] = genre
        plan.by_genre[genre] = plan.by_genre.get(genre, 0) + 1
        plan.by_source[source] = plan.by_source.get(source, 0) + 1
        if old != genre:
            plan.patched += 1
            plan.hits.append(
                GenreHit(
                    path=str(path),
                    crate=item.crate,
                    old=old,
                    new=genre,
                    source=source,
                )
            )
    for path, entry in entries.items():
        if path in assigned:
            continue
        genre, source = resolve_genre(path, entry)
        old = nml_genre(entry)
        if old == genre:
            continue
        plan.patched += 1
        plan.hits.append(
            GenreHit(
                path=str(path),
                crate="collection",
                old=old,
                new=genre,
                source=source,
            )
        )
    return plan, keepers, assigned


def write_genre_crates(
    stemit_folder,
    files: list[DiskFile],
    index: dict[Path, tuple[str, str]],
    assigned: dict[Path, str],
) -> None:
    """Replace STEMIT/Genres. Four role playlists per genre that has tracks."""
    genres_folder = _append_folder(stemit_folder, GENRES_FOLDER)
    subnodes = genres_folder.find("SUBNODES")
    if subnodes is None:
        return
    for child in list(subnodes):
        subnodes.remove(child)
    grouped: dict[str, dict[str, list[DiskFile]]] = defaultdict(
        lambda: {name: [] for name in PLAYLISTS}
    )
    for item in files:
        genre = assigned.get(item.path.resolve()) or UNTAGGED
        if item.crate in grouped[genre]:
            grouped[genre][item.crate].append(item)
    for genre in sorted(grouped, key=str.lower):
        folder = _append_folder(genres_folder, genre)
        for name in PLAYLISTS:
            playlist = _ensure_traktor_playlist(folder, name)
            count = 0
            for item in grouped[genre][name]:
                hit = index.get(item.path)
                if not hit:
                    continue
                pk_type, key = hit
                entry = ET.SubElement(playlist, "ENTRY")
                ET.SubElement(entry, "PRIMARYKEY", TYPE=pk_type, KEY=key)
                count += 1
            playlist.set("ENTRIES", str(count))


def assign_genres(
    files: list[DiskFile],
    stems_root: Path,
    nml: Path | None = None,
) -> dict[Path, str]:
    """Genre per keeper from current NML INFO (cleaned). Does not write NML."""
    nml_path = nml or TRAKTOR_NML
    entries: dict[Path, object] = {}
    if nml_path.is_file():
        collection = ET.parse(nml_path).getroot().find("COLLECTION")
        if collection is not None:
            entries = collection_by_path(collection, stems_root)
    assigned: dict[Path, str] = {}
    for item in files:
        path = item.path.resolve()
        genre, _source = resolve_genre(path, entries.get(path))
        assigned[path] = genre
    return assigned


def write_rekordbox_genre_crates(
    stemit_folder: ET.Element,
    files: list[DiskFile],
    index: dict[Path, str],
    assigned: dict[Path, str],
) -> int:
    """Append STEMIT/Genres under a Rekordbox STEMIT folder."""
    grouped: dict[str, dict[str, list[DiskFile]]] = defaultdict(
        lambda: {name: [] for name in PLAYLISTS}
    )
    for item in files:
        genre = assigned.get(item.path.resolve()) or UNTAGGED
        if item.crate in grouped[genre]:
            grouped[genre][item.crate].append(item)
    genres_folder = ET.SubElement(
        stemit_folder, "NODE", Name=GENRES_FOLDER, Type="0", Count="0"
    )
    genre_count = 0
    for genre in sorted(grouped, key=str.lower):
        folder = ET.SubElement(
            genres_folder, "NODE", Name=genre, Type="0", Count=str(len(PLAYLISTS))
        )
        for name in PLAYLISTS:
            keys = [
                index[item.path]
                for item in grouped[genre][name]
                if item.path in index
            ]
            node = ET.SubElement(
                folder,
                "NODE",
                Name=name,
                Type="1",
                KeyType="0",
                Entries=str(len(keys)),
            )
            for tid in keys:
                ET.SubElement(node, "TRACK", Key=tid)
        genre_count += 1
    genres_folder.set("Count", str(genre_count))
    return genre_count


def apply_genre_crates(
    nml_root,
    files: list[DiskFile],
    index: dict[Path, tuple[str, str]],
    stems_root: Path,
) -> GenreCratePlan:
    """Patch INFO GENRE on listed files and rebuild STEMIT/Genres."""
    collection = nml_root.find("COLLECTION")
    playlists = nml_root.find("PLAYLISTS")
    if collection is None or playlists is None:
        return GenreCratePlan()
    root_folder = playlists.find("NODE")
    if root_folder is None:
        return GenreCratePlan()
    entries = collection_by_path(collection, stems_root)
    assigned: dict[Path, str] = {}
    plan = GenreCratePlan(files=len(files))
    for item in files:
        path = item.path.resolve()
        entry = entries.get(path)
        genre, source = resolve_genre(path, entry)
        assigned[path] = genre
        plan.by_genre[genre] = plan.by_genre.get(genre, 0) + 1
        plan.by_source[source] = plan.by_source.get(source, 0) + 1
        if entry is None:
            continue
        old = nml_genre(entry)
        if old != genre:
            set_nml_genre(entry, genre)
            plan.patched += 1
            plan.hits.append(
                GenreHit(
                    path=str(path),
                    crate=item.crate,
                    old=old,
                    new=genre,
                    source=source,
                )
            )
    for path, entry in entries.items():
        if path in assigned:
            continue
        genre, source = resolve_genre(path, entry)
        old = nml_genre(entry)
        if old == genre:
            continue
        set_nml_genre(entry, genre)
        plan.patched += 1
        plan.hits.append(
            GenreHit(
                path=str(path),
                crate="collection",
                old=old,
                new=genre,
                source=source,
            )
        )
    stemit = _ensure_traktor_folder(root_folder, FOLDER_NAME)
    write_genre_crates(stemit, files, index, assigned)
    return plan


def format_genre_plan(plan: GenreCratePlan) -> str:
    lines = [
        f"stemit-genres: {plan.files} keepers  nml-patch {plan.patched}  "
        f"genres {len(plan.by_genre)}"
    ]
    if plan.by_source:
        lines.append(
            "  sources "
            + " ".join(f"{key}={count}" for key, count in sorted(plan.by_source.items()))
        )
    for name, count in sorted(plan.by_genre.items(), key=lambda kv: (-kv[1], kv[0].lower())):
        lines.append(f"  {count:5}  {name}")
    dirty = [hit for hit in plan.hits if hit.old.startswith("EDM") or hit.old.startswith("House,")]
    for hit in dirty[:8]:
        lines.append(f"  {hit.old}  →  {hit.new}")
    if len(dirty) > 8:
        lines.append(f"  … {len(dirty) - 8} more prefix cleanups")
    return "\n".join(lines)


def write_genre_report(plan: GenreCratePlan, extra: dict | None = None) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    payload = {
        "tool": "ix.crate.stemit-genres",
        "files": plan.files,
        "patched": plan.patched,
        "by_genre": plan.by_genre,
        "by_source": plan.by_source,
        "hits": [
            {
                "path": hit.path,
                "crate": hit.crate,
                "old": hit.old,
                "new": hit.new,
                "source": hit.source,
            }
            for hit in plan.hits[:500]
        ],
        **(extra or {}),
    }
    dest = REPORTS / f"stemit-genres-{stamp}.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest
