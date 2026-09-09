"""Local identity: filename, then tags. Lookups live in lookup.py."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ix_crate.families import ROLE_PAREN, Family, is_role_file, strip_role_markup
from ix_crate.paths import MISC_ALBUM, MISC_ARTIST

PLACEHOLDER_ARTISTS = {
    "",
    "unknown",
    "unknown artist",
    "various",
    "various artists",
    "va",
    "industrystems",
    "industry stems",
    "industry-stems",
    "industry stem",
}
PLACEHOLDER_ALBUMS = {
    "",
    "unknown",
    "unknown album",
    "album title goes here",
    "untitled album",
    "untitled",
}
PLACEHOLDER_TITLES = {
    "",
    "unknown",
    "unknown title",
    "track",
    "instrumental",
    "vocals",
    "drums",
    "bass",
    "other",
    "acapella",
    "a cappella",
}
JUNK_TITLE = re.compile(
    r"\s*\[(?:tuberipper\.cc|getmp3\.pro|official (?:video|audio|visualiser)[^\]]*|wubaholics premiere|nest hq premiere|this song is sick premiere|your edm premiere|headbang society premiere|clip)\]\s*",
    re.IGNORECASE,
)
JUNK_PARENS = re.compile(
    r"\s*\((?:official(?: music)? video(?: remastered)?|official montage video|official visualiser|lyric video|\d+\s*kbps)\)\s*",
    re.IGNORECASE,
)
RADIO_SUFFIX = re.compile(r"\s*__\s+.+$")
INVALID_FS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
TRACK_NUM = re.compile(r"^\d{1,2}(?:[.)\-]|)\s+")
# "1-07 Title" / "2.11 Title". Both sides capped at two digits so phone-number
# titles like "1-800-273-8255" are left alone.
DISC_TRACK = re.compile(r"^\d{1,2}[-.]\d{1,2}[.)]?\s+")
LEADING_ARTIST_NUM = re.compile(r"^(\d{2})\s+([A-Za-z].+)$")
NUMBERED_ARTIST_KEEP = re.compile(
    r"^(?:16 bit lolitas|28 east boyz|51 days|68 beats|95 north)\b",
    re.I,
)
MASHUP_MARK = re.compile(
    r"\b(?:mashup|megamashup|vs\.?|versus)\b| \+ | but every | but it is "
    r"|pomplamoose|wax audio|#mashup|dj schmolli|dj cummerbund| but ",
    re.IGNORECASE,
)
CLIP_MARK = re.compile(
    r"screenrecording|asdfmovie|bwav_test|birthday|tuberipper|mwclip",
    re.IGNORECASE,
)
PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)


def clean_text(part: str) -> str:
    text = strip_role_markup(part or "")
    text = JUNK_TITLE.sub(" ", text)
    text = JUNK_PARENS.sub(" ", text)
    text = RADIO_SUFFIX.sub("", text)
    text = re.sub(r"\s+", " ", text).strip(" ._-")
    return text


def sanitize(part: str, fallback: str) -> str:
    text = INVALID_FS.sub("_", clean_text(part))
    return text or fallback


BEATPORT_ID = re.compile(r"^(\d{6,9})_(.+)$")
_END = r"(?=_|\W|$)"
CONTRACTION_T = re.compile(
    r"(Don|It|I|Can|Won|Isn|Aren|Wasn|Wer|Let|That|What|Here|There|"
    r"He|She|We|They|You|Shouldn|Wouldn|Couldn|Didn|Doesn|Hasn|Haven|Hadn)_t"
    + _END,
    re.I,
)
CONTRACTION_S = re.compile(r"(It|That|What|Here|There|He|She|Let|Who)_s" + _END, re.I)
CONTRACTION_RE = re.compile(r"(We|They|You)_re" + _END, re.I)
CONTRACTION_LL = re.compile(r"(I|We|You|They|He|She)_ll" + _END, re.I)
CONTRACTION_VE = re.compile(r"(I|We|You|They)_ve" + _END, re.I)
CONTRACTION_M = re.compile(r"I_m" + _END, re.I)


def is_beatport_title(text: str) -> bool:
    """Beatport download name: ``12432715_Together_We_Fall_(Alexvnder_Remix)``."""
    return bool(BEATPORT_ID.match((text or "").strip()))


def pretty_beatport_title(text: str) -> str:
    """Strip the catalog id and turn underscores into a readable title."""
    raw = (text or "").strip()
    match = BEATPORT_ID.match(raw)
    body = match.group(2) if match else raw
    if "_" not in body:
        return body or raw
    body = CONTRACTION_T.sub(lambda m: m.group(1) + "'t", body)
    body = CONTRACTION_S.sub(lambda m: m.group(1) + "'s", body)
    body = CONTRACTION_RE.sub(lambda m: m.group(1) + "'re", body)
    body = CONTRACTION_LL.sub(lambda m: m.group(1) + "'ll", body)
    body = CONTRACTION_VE.sub(lambda m: m.group(1) + "'ve", body)
    body = CONTRACTION_M.sub("I'm", body)
    body = body.replace("_", " ")
    body = re.sub(r"\s+", " ", body).strip()
    return body or raw


def strip_track_number(title: str) -> str:
    text = (title or "").strip()
    # Multi-disc rips are named "1-07 Title". TRACK_NUM wants whitespace right
    # after the separator, so it never matched these and every disc-numbered
    # track failed to match its library row by title.
    text = DISC_TRACK.sub("", text)
    return TRACK_NUM.sub("", text).strip(" ._")


def strip_leading_track_artist(artist: str) -> str:
    """Remove mix-CD ``01 Artist`` prefixes. Keep 16 Bit Lolitas and similar."""
    text = (artist or "").strip()
    if NUMBERED_ARTIST_KEEP.match(text):
        return text
    match = LEADING_ARTIST_NUM.match(text)
    if not match:
        return text
    if int(match.group(1)) < 1 or int(match.group(1)) > 20:
        return text
    return clean_text(match.group(2))


def normalize_title(title: str) -> str:
    text = strip_track_number(clean_text(title)).lower()
    text = PUNCT.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text.startswith("the "):
        text = text[4:]
    return text


def titles_match(left: str, right: str) -> bool:
    a, b = normalize_title(left), normalize_title(right)
    if not a or not b:
        return False
    if a == b:
        return True
    longer, shorter = (a, b) if len(a) >= len(b) else (b, a)
    if not longer.startswith(shorter):
        return False
    rest = longer[len(shorter) :].strip(" -_")
    if not rest:
        return True
    if rest[:1] in {"(", "["}:
        return True
    first = rest.split()[0]
    return first in {
        "mix",
        "remix",
        "extended",
        "radio",
        "club",
        "original",
        "feat",
        "featuring",
        "ft",
        "pt",
        "part",
        "live",
        "edit",
        "version",
        "dub",
        "instrumental",
        "vocal",
    }


def is_mashup_name(text: str) -> bool:
    return bool(MASHUP_MARK.search(text or ""))


def is_clip_name(text: str) -> bool:
    return bool(CLIP_MARK.search(text or ""))


def duration_close(local: float | None, remote: float | None, *, slack: float = 8.0) -> bool:
    if local is None or remote is None:
        return False
    return abs(local - remote) <= max(slack, 0.08 * max(local, remote))


def is_placeholder_album_folder(name: str) -> bool:
    compact = re.sub(r"[_\s]+", " ", name or "").strip().lower()
    return compact in PLACEHOLDER_ALBUMS and compact != ""


def is_placeholder_artist(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_ARTISTS


def is_placeholder_title(value: str) -> bool:
    text = strip_role_markup(value).strip().lower()
    if text in PLACEHOLDER_TITLES or text.startswith("undefined"):
        return True
    raw = value.strip().lower()
    if raw in PLACEHOLDER_TITLES or raw.startswith("undefined"):
        return True
    if ROLE_PAREN.fullmatch(raw.strip()):
        return True
    if re.search(r"(?:^|[-._\s])track[-._\s]*\d{1,3}(?:[-._\s]+\d{1,3})?$", text):
        return True
    if re.match(r"rain[\s._-]+or[\s._-]+shine[\s._-]+summer", text):
        return True
    return False


def _read_tags(path: Path) -> tuple[str, str, str]:
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return "", "", ""
    try:
        audio = MutagenFile(path, easy=True)
    except Exception:
        return "", "", ""
    if audio is None or audio.tags is None:
        return "", "", ""
    tags = audio.tags

    def first(*keys: str) -> str:
        for key in keys:
            values = tags.get(key)
            if values:
                return str(values[0]).strip()
        return ""

    return first("albumartist", "artist"), first("album"), first("title")


def tags_from_family(family: Family) -> tuple[str, str, str]:
    """Prefer the mix file. Never trust a role-file title."""
    candidates: list[Path] = []
    mix = family.mix_file()
    if mix is not None:
        candidates.append(mix)
    for path in family.files:
        if path not in candidates:
            candidates.append(path)
    artist = album = title = ""
    for path in candidates:
        if is_role_file(path):
            continue
        a, al, t = _read_tags(path)
        if is_placeholder_title(t):
            t = ""
        if is_placeholder_artist(a):
            a = ""
        artist = artist or a
        album = album or al
        title = title or t
        if artist and title:
            break
    return artist, album, title


def split_sep(text: str, sep: str) -> list[str]:
    """Split on sep only outside parentheses."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
            buf.append(text[i])
            i += 1
            continue
        if text[i] == ")" and depth:
            depth -= 1
            buf.append(text[i])
            i += 1
            continue
        if depth == 0 and text.startswith(sep, i):
            parts.append("".join(buf).strip())
            buf = []
            i += len(sep)
            continue
        buf.append(text[i])
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [part for part in parts if part]


def split_dashes(text: str) -> list[str]:
    """Split on ' - ' only outside parentheses."""
    return split_sep(text, " - ")


MIX_ARTIST = re.compile(r"\b(?:mix|vol\.?|compilation|playlist|bootlegs?)\b", re.I)


def _short_artist(part: str) -> bool:
    """`_` / `|` only when the left side looks like a name, not a sentence."""
    return 0 < len(part.split()) <= 4


def _usable_filename_artist(part: str) -> bool:
    return bool(part) and _short_artist(part) and not MIX_ARTIST.search(part)


def parse_filename(key: str) -> tuple[str, str, str]:
    """Return (artist, album, title) from a family key."""
    cleaned = clean_text(strip_track_number(key))
    for sep in (" - ", " _ ", " | "):
        parts = [clean_text(part) for part in split_sep(cleaned, sep)]
        if len(parts) < 2 or not _usable_filename_artist(parts[0]):
            continue
        if len(parts) >= 3:
            return parts[0], parts[1], " - ".join(parts[2:])
        if len(parts) == 2:
            return parts[0], "", parts[1]
    return "", "", cleaned


def filename_hints_artist(key: str) -> bool:
    """True when the filename looks like it already names an artist."""
    artist, _, _ = parse_filename(key)
    if artist:
        return True
    cleaned = clean_text(strip_track_number(key))
    return any(sep in cleaned for sep in (" - ", " _ ", " | "))


@dataclass
class Identity:
    artist: str
    album: str
    title: str
    source: str
    movable: bool = True
    genre: str = ""

    @property
    def dest_artist(self) -> str:
        if self.source == "mashup":
            return "Compilations"
        if self.source == "outlier" or is_placeholder_artist(self.artist):
            return MISC_ARTIST
        return sanitize(self.artist, MISC_ARTIST)

    @property
    def dest_album(self) -> str:
        if self.source == "mashup":
            return f"Mashups/{sanitize(self.artist, 'Various Artists')}"
        if self.source == "outlier" or is_placeholder_artist(self.artist):
            return MISC_ALBUM
        if self.album.strip().lower() in PLACEHOLDER_ALBUMS:
            return "Singles"
        return sanitize(self.album, "Singles")


def identify(family: Family) -> Identity:
    """Filename first, then tags. No network."""
    tag_artist, tag_album, tag_title = tags_from_family(family)
    file_artist, file_album, file_title = parse_filename(family.key)

    artist = file_artist or tag_artist
    album = file_album or tag_album
    title = file_title or tag_title
    if tag_artist and not is_placeholder_artist(tag_artist) and is_placeholder_artist(file_artist):
        artist = tag_artist
    if tag_album and tag_album.strip().lower() not in PLACEHOLDER_ALBUMS and not file_album:
        album = tag_album
    if tag_title and not is_placeholder_title(tag_title) and (
        is_placeholder_title(file_title) or ".stem" in tag_title.lower()
    ):
        title = tag_title
    if is_placeholder_title(title) or ".stem" in (title or "").lower():
        title = file_title or tag_title

    artist, album, title = clean_text(artist), clean_text(album), clean_text(title)
    if is_placeholder_artist(artist):
        source = "local-gap"
    elif file_artist and artist == file_artist:
        source = "filename"
    else:
        source = "tags"

    return Identity(
        artist=artist,
        album=album,
        title=title,
        source=source,
        movable=True,
    )
