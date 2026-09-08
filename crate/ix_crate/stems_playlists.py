"""STEMIT crate playlists from ``stems_audio`` in any state.

Never writes Apple Music. Walks ``~/Music/stems_audio`` and rewrites
Traktor NML + Rekordbox XML crates from what is on disk — factory or
not. Files that are not yet in the collection get a location row so
the playlist can exist before Import / Analyze. Analyze stays in-app.

Crates: **Mixes** (the hardlink / parallel original), **Stems**,
**Acapellas**, **Instrumentals**.
"""

from __future__ import annotations

import shutil
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote

from ix_crate.families import STEM_SUFFIXES, is_role_file, strip_role_markup
from ix_crate.paths import AUDIO_EXTS, STEMS_AUDIO
from ix_crate.riff_repair import copy_number

PLAYLISTS = ("Mixes", "Stems", "Acapellas", "Instrumentals")
TRAKTOR_NML = (
    Path.home() / "Documents" / "Native Instruments" / "Traktor 4.5.1" / "collection.nml"
)
REKORDBOX_XML = Path.home() / "Music" / "PioneerDJ" / "rekordbox.xml"
FOLDER_NAME = "STEMIT"
KIND = {
    ".mp3": "MP3 File",
    ".m4a": "M4A File",
    ".wav": "WAV File",
    ".aiff": "AIFF File",
    ".aif": "AIFF File",
    ".flac": "FLAC File",
    ".mp4": "MP4 File",
}


@dataclass
class DiskFile:
    path: Path
    crate: str


@dataclass
class PlaylistSync:
    crate: str
    on_disk: int = 0
    in_collection: int = 0
    missing: list[str] = field(default_factory=list)


@dataclass
class SyncPlan:
    scanned: int = 0
    crates: dict[str, PlaylistSync] = field(default_factory=dict)
    traktor_nml: Path | None = None
    rekordbox_xml: Path | None = None
    added_traktor: int = 0
    added_rekordbox: int = 0


def classify(path: Path) -> str | None:
    """Which STEMIT crate a stems_audio file belongs in, if any."""
    name = path.name.lower()
    if any(name.endswith(suffix) for suffix in STEM_SUFFIXES):
        return "Stems"
    if ".stem" in name and path.suffix.lower() in {".m4a", ".mp4", ".mp3"}:
        return "Stems"
    if is_role_file(path):
        role = strip_role_markup(path.stem)
        leftover = path.stem[len(role) :].lower() if role else path.stem.lower()
        blob = leftover or name
        if "instrumental" in blob:
            return "Instrumentals"
        if any(token in blob for token in ("acapella", "acappella", "a cappella", "vocal", "vox")):
            return "Acapellas"
        return None
    if path.suffix.lower() in AUDIO_EXTS:
        return "Mixes"
    return None


def walk_stems(root: Path | None = None) -> list[DiskFile]:
    base = (root or STEMS_AUDIO).expanduser()
    found: list[DiskFile] = []
    if not base.is_dir():
        return found
    for path in base.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        if copy_number(path.stem) > 0:
            continue
        crate = classify(path)
        if crate:
            found.append(DiskFile(path=path.resolve(), crate=crate))
    found.sort(key=lambda item: (item.crate, str(item.path).lower()))
    return found


def filing_from_path(path: Path, root: Path) -> tuple[str, str, str]:
    """Artist / album / title from stems_audio/Artist/Album/file."""
    from ix_crate.role_titles import identity_for_role

    item = identity_for_role(path, root=root)
    if item.title:
        return item.artist, item.album, item.title
    try:
        rel = path.resolve().relative_to(root.expanduser().resolve())
    except ValueError:
        return "", "", strip_role_markup(path.stem)
    parts = list(rel.parts)
    artist = parts[0] if len(parts) > 1 else ""
    album = parts[1] if len(parts) > 2 else "Singles"
    title = strip_role_markup(path.stem) or path.stem
    return artist, album, title


def _loc_to_path(directory: str, file_attr: str) -> Path:
    decoded = unquote(file_attr or "")
    parts = [part for part in (directory or "").split("/:") if part]
    path = Path("/")
    for part in parts:
        path = path / part
    return (path / decoded).resolve() if decoded else path


def _traktor_dir_file(path: Path) -> tuple[str, str]:
    dir_parts = [part for part in path.parent.parts if part != "/"]
    return "/:" + "/:".join(dir_parts) + "/:", path.name


def _traktor_key(path: Path, volume: str = "Macintosh HD") -> tuple[str, str]:
    directory, file_attr = _traktor_dir_file(path)
    pk_type = "STEM" if ".stem." in path.name.lower() else "TRACK"
    return pk_type, f"{volume}{directory}{file_attr}"


def _rb_location(path: Path) -> str:
    posix = path.resolve().as_posix()
    if not posix.startswith("/"):
        posix = "/" + posix
    return "file://localhost" + quote(posix, safe="/")


def traktor_index(nml: Path) -> dict[Path, tuple[str, str]]:
    """path → (PRIMARYKEY TYPE, KEY) for live stems_audio entries."""
    tree = ET.parse(nml)
    collection = tree.getroot().find("COLLECTION")
    if collection is None:
        return {}
    index: dict[Path, tuple[str, str]] = {}
    for entry in collection.findall("ENTRY"):
        location = entry.find("LOCATION")
        if location is None:
            continue
        directory = location.get("DIR") or ""
        if "stems_audio" not in directory:
            continue
        file_attr = location.get("FILE") or ""
        volume = location.get("VOLUME") or "Macintosh HD"
        path = _loc_to_path(directory, file_attr)
        if not path.is_file():
            continue
        pk_type = "STEM" if ".stem." in path.name.lower() else "TRACK"
        key = f"{volume}{directory}{file_attr}"
        index[path] = (pk_type, key)
    return index


def rekordbox_index(xml: Path) -> dict[Path, str]:
    """path → TrackID for collection entries under stems_audio."""
    tree = ET.parse(xml)
    collection = tree.getroot().find("COLLECTION")
    if collection is None:
        return {}
    index: dict[Path, str] = {}
    for track in collection.findall("TRACK"):
        location = unquote((track.get("Location") or "").replace("file://localhost", ""))
        if "stems_audio" not in location:
            continue
        path = Path(location).resolve()
        tid = track.get("TrackID") or ""
        if tid and path.is_file():
            index[path] = tid
    return index


def plan_sync(
    *,
    stems_root: Path | None = None,
    nml: Path | None = None,
    xml: Path | None = None,
) -> tuple[SyncPlan, list[DiskFile]]:
    root = (stems_root or STEMS_AUDIO).expanduser()
    files = walk_stems(root)
    plan = SyncPlan(scanned=len(files))
    for name in PLAYLISTS:
        plan.crates[name] = PlaylistSync(crate=name)
    nml_path = nml or TRAKTOR_NML
    xml_path = xml or REKORDBOX_XML
    trakt = traktor_index(nml_path) if nml_path.is_file() else {}
    rekord = rekordbox_index(xml_path) if xml_path.is_file() else {}
    plan.traktor_nml = nml_path if nml_path.is_file() else None
    plan.rekordbox_xml = xml_path if xml_path.is_file() else None
    for item in files:
        crate = plan.crates[item.crate]
        crate.on_disk += 1
        if item.path in trakt or item.path in rekord:
            crate.in_collection += 1
        else:
            crate.missing.append(str(item.path))
    return plan, files


def _ensure_traktor_folder(root_folder: ET.Element, name: str) -> ET.Element:
    subnodes = root_folder.find("SUBNODES")
    if subnodes is None:
        subnodes = ET.SubElement(root_folder, "SUBNODES", COUNT="0")
    for node in subnodes.findall("NODE"):
        if node.get("TYPE") == "FOLDER" and node.get("NAME") == name:
            kids = node.find("SUBNODES")
            if kids is None:
                kids = ET.SubElement(node, "SUBNODES", COUNT="0")
            return node
    folder = ET.Element("NODE", TYPE="FOLDER", NAME=name)
    ET.SubElement(folder, "SUBNODES", COUNT="0")
    subnodes.insert(0, folder)
    subnodes.set("COUNT", str(len(list(subnodes))))
    return folder


def _prune_empty_playlist_nodes(folder: ET.Element, names: Iterable[str]) -> None:
    """Drop name-only playlist shells. Traktor shows the first Mixes node."""
    subnodes = folder.find("SUBNODES")
    if subnodes is None:
        return
    want = set(names)
    for node in list(subnodes.findall("NODE")):
        if node.get("TYPE") != "PLAYLIST" or node.get("NAME") not in want:
            continue
        if node.find("PLAYLIST") is None:
            subnodes.remove(node)
    subnodes.set("COUNT", str(len(list(subnodes))))


def _ensure_traktor_playlist(folder: ET.Element, name: str) -> ET.Element:
    subnodes = folder.find("SUBNODES")
    if subnodes is None:
        subnodes = ET.SubElement(folder, "SUBNODES", COUNT="0")
    for node in subnodes.findall("NODE"):
        if node.get("TYPE") == "PLAYLIST" and node.get("NAME") == name:
            playlist = node.find("PLAYLIST")
            if playlist is None:
                return ET.SubElement(
                    node,
                    "PLAYLIST",
                    ENTRIES="0",
                    TYPE="LIST",
                    UUID=uuid.uuid4().hex,
                )
            # ElementTree clear() also drops attributes. Traktor ignores a
            # PLAYLIST without TYPE="LIST" and UUID — STEMIT looks empty.
            uid = playlist.get("UUID") or uuid.uuid4().hex
            for child in list(playlist):
                playlist.remove(child)
            playlist.set("TYPE", "LIST")
            playlist.set("UUID", uid)
            playlist.set("ENTRIES", "0")
            return playlist
    node = ET.Element("NODE", TYPE="PLAYLIST", NAME=name)
    playlist = ET.SubElement(
        node, "PLAYLIST", ENTRIES="0", TYPE="LIST", UUID=uuid.uuid4().hex
    )
    subnodes.append(node)
    subnodes.set("COUNT", str(len(list(subnodes))))
    return playlist


def ensure_traktor_entries(
    files: Iterable[DiskFile],
    index: dict[Path, tuple[str, str]],
    collection: ET.Element,
    stems_root: Path,
) -> int:
    """Add NML location rows for stems_audio files the collection does not have."""
    added = 0
    for item in files:
        if item.path in index:
            continue
        artist, album, title = filing_from_path(item.path, stems_root)
        directory, file_attr = _traktor_dir_file(item.path)
        entry = ET.SubElement(collection, "ENTRY", TITLE=title, ARTIST=artist)
        ET.SubElement(
            entry,
            "LOCATION",
            DIR=directory,
            FILE=file_attr,
            VOLUME="Macintosh HD",
            VOLUMEID="Macintosh HD",
        )
        if album:
            ET.SubElement(entry, "ALBUM", TITLE=album)
        index[item.path] = _traktor_key(item.path)
        added += 1
    collection.set("ENTRIES", str(len(collection.findall("ENTRY"))))
    return added


def write_traktor(
    files: Iterable[DiskFile],
    index: dict[Path, tuple[str, str]],
    nml: Path,
    *,
    stems_root: Path | None = None,
) -> int:
    tree = ET.parse(nml)
    root = tree.getroot()
    collection = root.find("COLLECTION")
    if collection is None:
        raise RuntimeError("Traktor NML is missing COLLECTION")
    added = ensure_traktor_entries(
        files, index, collection, (stems_root or STEMS_AUDIO).expanduser()
    )
    playlists = root.find("PLAYLISTS")
    if playlists is None:
        raise RuntimeError("Traktor NML is missing PLAYLISTS")
    root_folder = playlists.find("NODE")
    if root_folder is None:
        raise RuntimeError("Traktor NML is missing $ROOT")
    folder = _ensure_traktor_folder(root_folder, FOLDER_NAME)
    _prune_empty_playlist_nodes(folder, PLAYLISTS)
    by_crate: dict[str, list[DiskFile]] = {name: [] for name in PLAYLISTS}
    for item in files:
        by_crate[item.crate].append(item)
    for name in PLAYLISTS:
        playlist = _ensure_traktor_playlist(folder, name)
        count = 0
        for item in by_crate[name]:
            hit = index.get(item.path)
            if not hit:
                continue
            pk_type, key = hit
            entry = ET.SubElement(playlist, "ENTRY")
            ET.SubElement(entry, "PRIMARYKEY", TYPE=pk_type, KEY=key)
            count += 1
        playlist.set("ENTRIES", str(count))
    backup = nml.with_suffix(nml.suffix + ".stemit.bak")
    shutil.copy2(nml, backup)
    tree.write(nml, encoding="UTF-8", xml_declaration=True)
    return added


def _rb_folder(playlists_root: ET.Element, name: str) -> ET.Element:
    root_node = playlists_root.find("NODE")
    if root_node is None:
        root_node = ET.SubElement(
            playlists_root, "NODE", Name="ROOT", Type="0", Count="0"
        )
    for node in root_node.findall("NODE"):
        if node.get("Name") == name and node.get("Type") == "0":
            for child in list(node):
                node.remove(child)
            return node
    folder = ET.SubElement(root_node, "NODE", Name=name, Type="0", Count="0")
    try:
        root_node.set("Count", str(int(root_node.get("Count") or "0") + 1))
    except ValueError:
        root_node.set("Count", str(len(root_node.findall("NODE"))))
    return folder


def ensure_rekordbox_entries(
    files: Iterable[DiskFile],
    index: dict[Path, str],
    collection: ET.Element,
    stems_root: Path,
) -> int:
    """Add rekordbox.xml location rows for stems_audio files not yet imported."""
    used = {int(tid) for tid in index.values() if str(tid).isdigit()}
    for track in collection.findall("TRACK"):
        tid = track.get("TrackID") or ""
        if tid.isdigit():
            used.add(int(tid))
    next_id = (max(used) + 1) if used else 900000000
    added = 0
    for item in files:
        if item.path in index:
            continue
        while next_id in used:
            next_id += 1
        artist, album, title = filing_from_path(item.path, stems_root)
        tid = str(next_id)
        used.add(next_id)
        next_id += 1
        suffix = item.path.suffix.lower()
        kind = "M4A File" if ".stem." in item.path.name.lower() else KIND.get(suffix, "M4A File")
        ET.SubElement(
            collection,
            "TRACK",
            TrackID=tid,
            Name=title,
            Artist=artist,
            Album=album,
            Kind=kind,
            Size=str(item.path.stat().st_size),
            Location=_rb_location(item.path),
        )
        index[item.path] = tid
        added += 1
    collection.set("Entries", str(len(collection.findall("TRACK"))))
    return added


def write_rekordbox(
    files: Iterable[DiskFile],
    index: dict[Path, str],
    xml: Path,
    *,
    stems_root: Path | None = None,
) -> int:
    tree = ET.parse(xml)
    root = tree.getroot()
    collection = root.find("COLLECTION")
    if collection is None:
        collection = ET.SubElement(root, "COLLECTION", Entries="0")
    added = ensure_rekordbox_entries(
        files, index, collection, (stems_root or STEMS_AUDIO).expanduser()
    )
    playlists = root.find("PLAYLISTS")
    if playlists is None:
        playlists = ET.SubElement(root, "PLAYLISTS")
    folder = _rb_folder(playlists, FOLDER_NAME)
    by_crate: dict[str, list[DiskFile]] = {name: [] for name in PLAYLISTS}
    for item in files:
        by_crate[item.crate].append(item)
    count = 0
    for name in PLAYLISTS:
        keys = [index[item.path] for item in by_crate[name] if item.path in index]
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
        count += 1
    folder.set("Count", str(count))
    backup = xml.with_suffix(xml.suffix + ".stemit.bak")
    shutil.copy2(xml, backup)
    tree.write(xml, encoding="UTF-8", xml_declaration=True)
    return added


def rebuild_stemit_nml(
    nml: Path | None = None,
    *,
    stems_root: Path | None = None,
) -> int:
    """Rewrite Traktor STEMIT crates only. Does not touch rekordbox.xml."""
    nml_path = nml or TRAKTOR_NML
    root = (stems_root or STEMS_AUDIO).expanduser()
    files = walk_stems(root)
    return write_traktor(files, traktor_index(nml_path), nml_path, stems_root=root)


def sync_playlists(
    *,
    execute: bool,
    stems_root: Path | None = None,
    nml: Path | None = None,
    xml: Path | None = None,
) -> SyncPlan:
    plan, files = plan_sync(stems_root=stems_root, nml=nml, xml=xml)
    if not execute:
        return plan
    root = (stems_root or STEMS_AUDIO).expanduser()
    if plan.traktor_nml:
        plan.added_traktor = write_traktor(
            files, traktor_index(plan.traktor_nml), plan.traktor_nml, stems_root=root
        )
    if plan.rekordbox_xml:
        plan.added_rekordbox = write_rekordbox(
            files, rekordbox_index(plan.rekordbox_xml), plan.rekordbox_xml, stems_root=root
        )
    return plan


def format_plan(plan: SyncPlan) -> str:
    lines = [
        f"STEMIT crates from stems_audio: {plan.scanned} files on disk",
    ]
    for name in PLAYLISTS:
        crate = plan.crates[name]
        lines.append(
            f"  {name:14} on disk {crate.on_disk:5}  already in collection {crate.in_collection:5}  "
            f"will add {len(crate.missing):5}"
        )
    if plan.traktor_nml is None:
        lines.append("  Traktor NML not found — playlist write skipped")
    if plan.rekordbox_xml is None:
        lines.append("  Rekordbox XML not found — playlist write skipped")
    if plan.added_traktor or plan.added_rekordbox:
        lines.append(
            f"  added collection rows  Traktor {plan.added_traktor}  Rekordbox {plan.added_rekordbox}"
        )
    return "\n".join(lines)
