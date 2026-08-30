"""Library roots. Never hardcode /Users/<name>/."""

from __future__ import annotations

from pathlib import Path

STEMS_AUDIO = Path.home() / "Music" / "stems_audio"
APPLE_MUSIC = Path.home() / "Music" / "Music" / "Media.localized"
UNKNOWN_ARTIST = STEMS_AUDIO / "Unknown Artist"
UNKNOWN_ALBUM = UNKNOWN_ARTIST / "Unknown Album"
UNKNOWN_MASHUPS = UNKNOWN_ARTIST / "Mashups"
REPORTS = Path.home() / "local_tools" / "crate" / "reports"
CACHE = Path.home() / "local_tools" / "crate" / "lookup-cache.json"
OUTLIERS_ARTIST = "_outliers"
OUTLIERS_ALBUM = "Inbox"
OUTLIERS_INBOX = STEMS_AUDIO / OUTLIERS_ARTIST / OUTLIERS_ALBUM
MISC_ARTIST = "Compilations"
MISC_ALBUM = "Mashups/Miscellaneous"
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434

AUDIO_EXTS = {
    ".mp3",
    ".wav",
    ".aiff",
    ".aif",
    ".flac",
    ".m4a",
    ".aac",
    ".alac",
    ".ogg",
    ".wma",
    ".mp4",
}

STEM_SUFFIXES = (".stem.m4a", ".stem.mp4", ".stem.mp3")
ROLE_SUFFIXES = (
    "vocals",
    "instrumental",
    "drums",
    "bass",
    "other",
    "acapella",
    "a cappella",
    "acappella",
)
