"""Catalog + Ollama lookups. Loopback only for Ollama. Cache off-repo."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from ix_crate.families import Family
from ix_crate.identify import (
    Identity,
    clean_text,
    duration_close,
    identify,
    is_clip_name,
    is_mashup_name,
    is_placeholder_artist,
    is_placeholder_title,
    strip_track_number,
    titles_match,
)
from ix_crate.paths import CACHE, OLLAMA_HOST, OLLAMA_PORT

MB_URL = "https://musicbrainz.org/ws/2/recording/"
ITUNES_URL = "https://itunes.apple.com/search"
DEEZER_URL = "https://api.deezer.com/search"
UA = "ix-crate/0.2 (https://github.com/ixamal/ix)"
OLLAMA_MODEL = "qwen2.5:7b"
SHORT_CATALOG_TITLE = 10
MB_GAP = 1.1
CATALOG_GAP = 0.35
LONG_MIX_SEC = 20 * 60


def _ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def _urlopen(req: urllib.request.Request, timeout: int = 20):
    return urllib.request.urlopen(req, timeout=timeout, context=_ssl_context())


def _load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")


def _http_json(url: str, cache: dict, key: str, *, gap: float) -> dict | list | None:
    if key in cache:
        return cache[key]
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        time.sleep(gap)
        with _urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ssl.SSLError):
        cache[key] = None
        _save_cache(cache)
        return None
    cache[key] = payload
    _save_cache(cache)
    return payload


def search_query(title: str, artist: str = "") -> str:
    title = strip_track_number(clean_text(title))
    artist = clean_text(artist)
    if artist and not is_placeholder_artist(artist):
        return f"{artist} {title}".strip()
    return title


def pick_catalog_hit(
    hits: list[dict], query_title: str, local_duration: float | None
) -> dict | None:
    titled = [hit for hit in hits if titles_match(query_title, str(hit.get("title") or ""))]
    if not titled:
        return None
    timed = [
        hit
        for hit in titled
        if duration_close(local_duration, hit.get("duration"))
    ]
    if timed:
        hit = dict(timed[0])
        hit["duration_match"] = True
        return hit
    return None


def itunes_search(query: str, cache: dict) -> list[dict]:
    if not query:
        return []
    key = f"itunes::v2::{query.lower()}"
    url = ITUNES_URL + "?" + urllib.parse.urlencode(
        {"term": query, "entity": "song", "limit": "8"}
    )
    payload = _http_json(url, cache, key, gap=CATALOG_GAP)
    if not isinstance(payload, dict):
        return []
    hits = []
    for item in payload.get("results") or []:
        millis = item.get("trackTimeMillis")
        hits.append(
            {
                "artist": clean_text(str(item.get("artistName") or "")),
                "album": clean_text(str(item.get("collectionName") or "")),
                "title": clean_text(str(item.get("trackName") or "")),
                "duration": (millis / 1000.0) if millis else None,
                "genre": clean_text(str(item.get("primaryGenreName") or "")),
                "source": "itunes",
            }
        )
    return hits


def deezer_search(query: str, cache: dict) -> list[dict]:
    if not query:
        return []
    key = f"deezer::{query.lower()}"
    url = DEEZER_URL + "?" + urllib.parse.urlencode({"q": query, "limit": "8"})
    payload = _http_json(url, cache, key, gap=CATALOG_GAP)
    if not isinstance(payload, dict):
        return []
    hits = []
    for item in payload.get("data") or []:
        artist = (item.get("artist") or {}).get("name")
        album = (item.get("album") or {}).get("title")
        hits.append(
            {
                "artist": clean_text(str(artist or "")),
                "album": clean_text(str(album or "")),
                "title": clean_text(str(item.get("title") or "")),
                "duration": float(item["duration"]) if item.get("duration") else None,
                "source": "deezer",
            }
        )
    return hits


def artists_match(left: str, right: str) -> bool:
    a, b = clean_text(left).lower(), clean_text(right).lower()
    if not a or not b:
        return False
    return a == b or a in b or b in a


def catalog_identify(title: str, artist: str, duration: float | None, cache: dict) -> dict | None:
    query = search_query(title, artist)
    if len(query) < 4:
        return None
    itunes_best = pick_catalog_hit(itunes_search(query, cache), title, duration)
    deezer_best = pick_catalog_hit(deezer_search(query, cache), title, duration)
    if itunes_best and deezer_best and artists_match(
        itunes_best["artist"], deezer_best["artist"]
    ):
        hit = dict(itunes_best)
        hit["source"] = "itunes+deezer"
        return hit
    if itunes_best and itunes_best.get("duration_match"):
        return itunes_best
    if deezer_best and deezer_best.get("duration_match"):
        return deezer_best
    return None


def musicbrainz_search(artist: str, title: str, cache: dict) -> dict | None:
    title = clean_text(title)
    artist = clean_text(artist)
    if not title:
        return None
    key = f"mb::{artist.lower()}::{title.lower()}"
    if key in cache:
        return cache[key]
    parts = [f'recording:"{title}"']
    if artist and not is_placeholder_artist(artist):
        parts.append(f'artist:"{artist}"')
    query = " AND ".join(parts)
    url = MB_URL + "?" + urllib.parse.urlencode({"query": query, "fmt": "json", "limit": "5"})
    payload = _http_json(url, cache, key, gap=MB_GAP)
    if not isinstance(payload, dict):
        return None
    recordings = payload.get("recordings") or []
    if not recordings:
        cache[key] = None
        _save_cache(cache)
        return None
    rec = recordings[0]
    credit = rec.get("artist-credit") or [{}]
    found_artist = ""
    if credit:
        found_artist = str(credit[0].get("name") or credit[0].get("artist", {}).get("name") or "")
    releases = rec.get("releases") or []
    found_album = str(releases[0].get("title") or "") if releases else ""
    hit = {
        "artist": clean_text(found_artist),
        "album": clean_text(found_album),
        "title": clean_text(str(rec.get("title") or title)),
        "score": rec.get("score"),
    }
    cache[key] = hit
    _save_cache(cache)
    return hit


def listed_models() -> list[str]:
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    return [str(item.get("name") or "") for item in payload.get("models") or []]


def pick_ollama_model() -> str | None:
    """Coder models stay off music ID. Prefer OLLAMA_MODEL, then qwen2.5:7b."""
    import os

    names = listed_models()
    if not names:
        return None
    wanted = os.environ.get("OLLAMA_MODEL") or OLLAMA_MODEL
    if "coder" in wanted.lower():
        wanted = OLLAMA_MODEL
    for name in names:
        if wanted in name or name.startswith(wanted):
            return name
    for name in names:
        if "coder" not in name.lower():
            return name
    return None


def ollama_ready(model: str) -> bool:
    return bool(model) and "coder" not in model.lower()


def artist_named_in_text(artist: str, blob: str) -> bool:
    """Refuse invented famous artists. Every 3+ letter token must appear in the filename."""
    if is_placeholder_artist(artist):
        return False
    hay = (blob or "").lower()
    if artist.lower() in hay:
        return True
    tokens = [tok for tok in re.findall(r"[a-z0-9]+", artist.lower()) if len(tok) >= 3]
    return bool(tokens) and all(tok in hay for tok in tokens)


def catalog_worth_query(title: str, artist: str) -> bool:
    query = search_query(title, artist)
    if len(query) < 4:
        return False
    if is_placeholder_artist(artist) and len(query.split()) < 2 and len(query) < SHORT_CATALOG_TITLE:
        return False
    return True


def ollama_infer(family_key: str, artist: str, album: str, title: str, cache: dict) -> dict | None:
    model = pick_ollama_model()
    if not ollama_ready(model or ""):
        return None
    key = f"ollama::{model}::{family_key.lower()}"
    if key in cache:
        return cache[key]
    prompt = (
        "You are a music librarian. Given a DJ filename and any tags, "
        "return JSON only with keys artist, album, title, outlier. "
        "outlier is true for movie clips, birthday songs, memes, screen recordings, tests, "
        "one-word bootlegs, or when the artist is not clearly named. "
        "If outlier, artist must be empty. album may be empty. title is a short clean name. "
        "Do not invent famous artists unless the filename clearly names them.\n"
        f"filename: {family_key}\nartist: {artist}\nalbum: {album}\ntitle: {title}\n"
    )
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
    ).encode("utf-8")
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        raw = payload.get("response") or "{}"
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        cache[key] = None
        _save_cache(cache)
        return None
    if not isinstance(data, dict):
        cache[key] = None
        _save_cache(cache)
        return None
    hit = {
        "artist": clean_text(str(data.get("artist") or "")),
        "album": clean_text(str(data.get("album") or "")),
        "title": clean_text(str(data.get("title") or "")),
        "outlier": bool(data.get("outlier")),
    }
    cache[key] = hit
    _save_cache(cache)
    return hit


def _outlier(title: str) -> Identity:
    return Identity(
        artist="",
        album="",
        title=clean_text(title) or "untitled",
        source="outlier",
        movable=True,
    )


def resolve(family: Family, *, lookup: bool = True) -> Identity:
    """filename → tags → iTunes/Deezer → MusicBrainz → Ollama → Miscellaneous."""
    local = identify(family)
    artist, album, title = local.artist, local.album, local.title
    source = local.source
    blob = " ".join([family.key, artist, album, title])
    duration = family.mix_duration()
    clip = is_clip_name(blob)
    mashup = is_mashup_name(blob)
    long_mix = duration is not None and duration >= LONG_MIX_SEC
    skip_catalog = clip or mashup or long_mix

    cache = _load_cache() if lookup else {}

    needs_catalog = (
        lookup
        and not skip_catalog
        and (is_placeholder_artist(artist) or is_placeholder_title(title))
        and catalog_worth_query(title or family.key, artist)
    )
    if needs_catalog:
        print(f"  catalog: {family.key[:80]}", flush=True)
        hit = catalog_identify(title or family.key, artist, duration, cache)
        if hit and hit.get("artist"):
            artist = hit["artist"]
            album = hit.get("album") or album
            title = hit.get("title") or title
            source = hit.get("source") or "catalog"

    needs_mb = lookup and artist and not is_placeholder_artist(artist) and not album
    if needs_mb and title:
        print(f"  musicbrainz: {family.key[:80]}", flush=True)
        hit = musicbrainz_search(artist, title, cache)
        if hit and (hit.get("score") is None or int(hit.get("score") or 0) >= 80):
            if not album and hit.get("album"):
                album = hit["album"]
                if source == "local-gap":
                    source = "musicbrainz"

    if lookup and is_placeholder_artist(artist):
        hit = ollama_infer(family.key, artist, album, title, cache)
        if hit:
            print(f"  ollama: {family.key[:80]}", flush=True)
            named = artist_named_in_text(str(hit.get("artist") or ""), family.key)
            if hit.get("outlier") or not named:
                return _outlier(hit.get("title") or family.key)
            artist = hit["artist"]
            album = hit.get("album") or album
            title = hit.get("title") or title
            source = "ollama"

    if is_placeholder_artist(artist) or not clean_text(title):
        return _outlier(title or family.key)
    return Identity(
        artist=artist,
        album=album,
        title=title or clean_text(family.key),
        source=source,
        movable=True,
    )
