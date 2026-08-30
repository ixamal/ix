"""Parse mashup credits and dest: Compilations/Mashups/{Artist}/."""

from __future__ import annotations

import re

from ix_crate.families import Family
from ix_crate.identify import (
    Identity,
    clean_text,
    is_clip_name,
    is_mashup_name,
    is_placeholder_album_folder,
    is_placeholder_artist,
    parse_filename,
    tags_from_family,
)

KNOWN_MASHERS = (
    ("wax audio", "Wax Audio"),
    ("pomplamoose", "Pomplamoose"),
    ("paolo monti", "Paolo Monti"),
    ("dj scooter funk", "DJ Scooter Funk"),
    ("dj schmolli", "DJ Schmolli"),
    ("dj cummerbund", "DJ Cummerbund"),
    ("yitt", "YITT"),
)
SKIP_PARENTS = {"mashups", "mashup", "unknown artist", "unknown album", "compilations", "inbox"}
MASHUP_BY = re.compile(r"\s+by\s+([A-Z][\w .']{1,40})$")
MASHUP_OF = re.compile(r"mashup of\s+(.+)$", re.IGNORECASE)
EMDASH_ARTISTS = re.compile(r"[–—]\s*(.+)$")
AFTER_DASH_VS = re.compile(r"\s+-\s+(.+\bvs\.?\b.+)$", re.IGNORECASE)
LEAD_VS = re.compile(
    r"^(.+?\bvs\.?\b.+?)(?:\s+-\s+|\s*[-–:]\s+)",
    re.IGNORECASE,
)
PAREN_VS = re.compile(r"\(([^)]*\bvs\.?\b[^)]*)\)", re.IGNORECASE)
WHOLE_VS = re.compile(r"^.+\bvs\.?\b.+$", re.IGNORECASE)
NAMED_MASHUP = re.compile(r"^(.+?)\s+mashup\s*$", re.IGNORECASE)
FEAT_PAIR = re.compile(r"^(.+\bfeat\.?\b.+)$", re.IGNORECASE)
PIPE_SPLIT = re.compile(r"\s+[|_]\s+")


def _looks_like_credit(text: str) -> bool:
    low = text.lower()
    if re.search(r"\b(mashup|megamashup|remix|reboot|summer|but)\b", low):
        return False
    words = text.split()
    return 1 <= len(words) <= 6


def parse_mashup_artist(key: str, tag_artist: str = "") -> str:
    if tag_artist and not is_placeholder_artist(tag_artist):
        return clean_text(tag_artist)
    text = clean_text(key)
    low = text.lower()
    for needle, name in KNOWN_MASHERS:
        if needle in low:
            return name
    if " by " in text:
        credit = text.rsplit(" by ", 1)[-1]
        if _looks_like_credit(credit):
            return clean_text(credit)
    by_hit = MASHUP_BY.search(text)
    if by_hit and _looks_like_credit(by_hit.group(1)):
        return clean_text(by_hit.group(1))
    of_hit = MASHUP_OF.search(text)
    if of_hit:
        return clean_text(of_hit.group(1).replace("/", " x ").replace("_", " x "))
    dash = EMDASH_ARTISTS.search(text)
    if dash and re.search(r"\bx\b|\bvs\.?\b", dash.group(1), re.IGNORECASE):
        return clean_text(dash.group(1))
    paren = PAREN_VS.search(text)
    if paren:
        inner = re.sub(r"\s*mashup.*$", "", paren.group(1), flags=re.IGNORECASE)
        return clean_text(inner)
    after = AFTER_DASH_VS.search(text)
    if after:
        return clean_text(after.group(1))
    lead = LEAD_VS.search(text)
    if lead:
        return clean_text(lead.group(1))
    named = NAMED_MASHUP.match(text)
    if named and _looks_like_credit(named.group(1)) and "_" not in named.group(1):
        return clean_text(named.group(1))
    feat_after = re.search(r"\s+-\s+(.+\bfeat\.?\b.+)$", text, re.IGNORECASE)
    if feat_after:
        return clean_text(feat_after.group(1))
    vs_only = re.sub(r"\s*\([^)]+\)$", "", text)
    vs_only = re.sub(r"\s*mashup\)?\s*$", "", vs_only, flags=re.IGNORECASE)
    if WHOLE_VS.match(vs_only) and len(vs_only) <= 70:
        return clean_text(vs_only)
    if WHOLE_VS.match(text) and len(text) <= 70:
        return text
    feat = FEAT_PAIR.match(text)
    if feat and len(text.split()) <= 8:
        return text
    parts = PIPE_SPLIT.split(text)
    if len(parts) >= 2:
        tail = clean_text(parts[-1])
        head = clean_text(parts[0])
        if _looks_like_credit(tail):
            return tail
        if _looks_like_credit(head):
            return head
    return "Various Artists"


def parent_is_mashup(parent: str) -> bool:
    low = (parent or "").strip().lower()
    if low in SKIP_PARENTS:
        return False
    if any(needle in low for needle, _ in KNOWN_MASHERS):
        return True
    return is_mashup_name(parent)


def dest_mashup_artist(key: str, parent: str, tag_artist: str = "") -> str:
    parent_clean = clean_text((parent or "").replace("_", "/"))
    if parent_clean and parent_clean.lower() not in SKIP_PARENTS:
        return parent_clean
    file_artist, _, _ = parse_filename(key)
    if file_artist and not is_placeholder_artist(file_artist):
        return clean_text(file_artist)
    if tag_artist and not is_placeholder_artist(tag_artist):
        return clean_text(tag_artist)
    return parse_mashup_artist(key, tag_artist)


def identify_mashup(
    family: Family, *, force: bool = False, parent: str = ""
) -> Identity | None:
    if not force and is_clip_name(family.key):
        return None
    tag_artist, _, tag_title = tags_from_family(family)
    blob = " ".join([family.key, tag_artist, tag_title, parent])
    if not force and not parent_is_mashup(parent):
        if not is_mashup_name(blob) and not is_mashup_name(family.key):
            return None
    artist = dest_mashup_artist(family.key, parent, tag_artist)
    title = clean_text(tag_title or family.key) or family.key
    return Identity(
        artist=artist,
        album="Mashups",
        title=title,
        source="mashup",
        movable=True,
    )

