"""Group mix + stem + role siblings so they always move together."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ix_crate.paths import AUDIO_EXTS, ROLE_SUFFIXES, STEM_SUFFIXES

ROLE_ALT = "|".join(re.escape(role) for role in ROLE_SUFFIXES)
ROLE_TAIL = re.compile(rf"\s+-\s+({ROLE_ALT})$", re.IGNORECASE)
ROLE_UNDERSCORE = re.compile(rf"_({ROLE_ALT})$", re.IGNORECASE)
ROLE_PAREN = re.compile(rf"\s*\(({ROLE_ALT})\)\s*$", re.IGNORECASE)
STEM_LEFTOVER = re.compile(r"\.stem$", re.IGNORECASE)
CONTAINER_LEFTOVER = re.compile(r"\.(?:wmv|avi|mov|mkv)$", re.IGNORECASE)


def strip_role_markup(name: str) -> str:
    """Drop role / leftover container tokens from a basename or family key."""
    text = name.strip()
    text = STEM_LEFTOVER.sub("", text)
    text = CONTAINER_LEFTOVER.sub("", text)
    text = ROLE_TAIL.sub("", text)
    text = ROLE_UNDERSCORE.sub("", text)
    text = ROLE_PAREN.sub("", text)
    return text.strip()


def basename_without_container(path: Path) -> str:
    name = path.name
    lower = name.lower()
    for suffix in STEM_SUFFIXES:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def is_role_file(path: Path) -> bool:
    name = basename_without_container(path)
    return name != strip_role_markup(name)


def is_audio(path: Path) -> bool:
    if not path.is_file() or path.name.startswith("."):
        return False
    lower = path.name.lower()
    if any(lower.endswith(suffix) for suffix in STEM_SUFFIXES):
        return True
    return path.suffix.lower() in AUDIO_EXTS


def family_key(path: Path) -> str:
    name = path.name
    lower = name.lower()
    for suffix in STEM_SUFFIXES:
        if lower.endswith(suffix):
            name = name[: -len(suffix)]
            break
    else:
        name = path.stem
    return strip_role_markup(name)


@dataclass
class Family:
    key: str
    files: list[Path] = field(default_factory=list)

    def mix_file(self) -> Path | None:
        ranked = []
        for path in self.files:
            lower = path.name.lower()
            if is_role_file(path):
                continue
            if any(lower.endswith(suffix) for suffix in STEM_SUFFIXES):
                ranked.append((2, path))
            elif path.suffix.lower() in {".mp3", ".wav", ".aif", ".aiff", ".flac", ".aac"}:
                ranked.append((0, path))
            else:
                ranked.append((1, path))
        ranked.sort(key=lambda item: (item[0], item[1].name))
        return ranked[0][1] if ranked else (self.files[0] if self.files else None)

    def mix_duration(self) -> float | None:
        mix = self.mix_file()
        if mix is None:
            return None
        try:
            from mutagen import File as MutagenFile
        except ImportError:
            return None
        try:
            audio = MutagenFile(mix)
        except Exception:
            return None
        if audio is None or audio.info is None:
            return None
        length = getattr(audio.info, "length", None)
        return float(length) if length else None


def discover_families(root: Path) -> list[Family]:
    buckets: dict[str, list[Path]] = {}
    for path in sorted(root.iterdir()):
        if not is_audio(path):
            continue
        buckets.setdefault(family_key(path), []).append(path)
    return [Family(key=key, files=files) for key, files in sorted(buckets.items())]
