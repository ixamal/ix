# Mac apps: Crate ID and Crate Bridge

Planning only. No `crate/ix_crate` code moves in this pass.

**For performers:** two signed, notarized `.dmg`s. Drop a folder (or point at a playlist / library XML). Preview. Apply. Undo. No Python install, no `PYTHONPATH`.

**For developers:** a parallel tree (`packages/`) that extracts a path-free core from the crate toolkit, then ships one Mac app per product (CLI + drag-and-drop UI). The owner's existing Python + AppleScript stay exactly where they are.

## Constraint (frozen)

Leave `crate/ix_crate/` alone. CRATER, BABYLON, STEMIT, Music.app AppleScript, Mixed In Key crates, and the nightly reports under `~/local_tools/crate/` keep working. David keeps augmenting those scripts.

Ship products next to them, not instead of them.

Repo license stays **Apache-2.0**. Open-source first. GitHub Sponsors / Ko-fi optional. A later $5–10 **Crate Bridge** signed build is a convenience fee for the same source, not a closed fork.

## Why a parallel tree

`crate/` is a booth-local toolkit. It assumes this Mac:

| Hard-coded today | Where |
| --- | --- |
| `~/Music/stems_audio`, `~/Music/Music/Media.localized` | `paths.py` |
| `~/local_tools/crate/reports`, `lookup-cache.json` | `paths.py` |
| Traktor `Documents/Native Instruments/Traktor 4.5.1/collection.nml` | `stems_playlists.py` |
| `~/Music/PioneerDJ/rekordbox.xml` | `stems_playlists.py` |
| NML `VOLUME="Macintosh HD"` | `crates.py` ingest |
| `fpcalc` via `PATH` then `/opt/homebrew/bin/fpcalc` | `acoustid.py` |
| Shazam in `~/local_tools/crate/shazam-venv` (Python 3.12; Homebrew 3.14 segfaults `shazamio-core`) | `shazam.py` |
| Ollama `127.0.0.1:11434` | `lookup.py` / `paths.py` |
| Music.app must be open; `osascript` | `music_fix.py`, `crates.py`, `music_dupes.py` |
| Safety: refuse paths outside `stems_audio` / refuse `Media.localized` | `safety.py` |

A downloadable app cannot carry any of that. It takes a folder (or library file) the user dropped.

## Layout

```
packages/
  crate_core/          shared identify + tag + playlist XML/NML (no Music.app, no home paths)
  crateid/             Product 1 — CLI + PySide6 app
  cratebridge/         Product 2 — CLI + PySide6 app
  dist/                py2app/PyInstaller specs, entitlements, create-dmg, Sparkle bits
```

`app/` is fine if we later want a Swift shell. Start with `packages/` so the shared core is a real Python package.

**v1 import policy:** `crate/ix_crate` does **not** import `packages/crate_core`. Duplicate the extract, then optionally thin-wrap later. First breakage of `music-fix` / CRATER is not worth a shared import.

Tests for the products live under `packages/*/tests/` and copy the existing cases from `crate/tests/test_identify.py`, `test_music_fix.py` (identity only), `test_crates.py`, `test_xml_io.py`. Do not rewrite the crate suite.

---

## Product 1 — Crate ID (free)

Identify-and-tag a folder of audio. No Music.app. No file moves. No Discogs. No STEMIT.

Owner analogue: `music-fix` (`resolve()` + `write_file_tags`) minus AppleScript library writes and minus `plan.py` family rehomes.

### Cascade (from `lookup.resolve`)

Default **strict** (safe for strangers). **Aggressive** is a checkbox, off unless the user turns it on.

1. Filename — `identify.parse_filename` (`Artist - Title`, `Artist - Album - Title`; `_` / `|` only when the left side is ≤4 words). Junk strip in `identify.clean_text`.
2. Tags — mix-file only (`identify.tags_from_family`). Ignore role-file titles (`instrumental` / `vocals`). Placeholders in `PLACEHOLDER_*`.
3. AcoustID — `acoustid.acoustid_identify` via bundled `fpcalc`. Aggressive only. Never submit fingerprints.
4. iTunes + Deezer — `catalog_identify`. Title + duration, or both catalogs agree on artist. Skip mashups, clips, mixes ≥20 min (`LONG_MIX_SEC`).
5. MusicBrainz — album fill when artist is already known (`musicbrainz_search`, score ≥80). Aggressive: duration search when artist is still empty.
6. Shazam — **opt-in, off by default.** See licensing.
7. Ollama — **omit from the app.** Loopback-only, model-dependent, owner-machine. Keep it in `crate/`.

Unidentified leftovers stay untouched. Do not salvage as Various Artists (`music-fix` already refuses this).

### Extract into `crate_core` (no home paths)

| Module | Take | Leave / rewrite |
| --- | --- | --- |
| `identify.py` | parse/clean/placeholders, `Identity` **without** `dest_artist` / `dest_album` (those file under `Compilations/` for `plan.py`) | `MISC_ARTIST` / `MISC_ALBUM` from `paths.py` |
| `families.py` | `Family`, `family_key`, role/stem grouping, `mix_duration` | none; already path-free |
| `lookup.py` | catalog, MusicBrainz, `resolve` with injected cache + HTTP + rate limits | `CACHE` path, `print()` progress, Ollama, `OLLAMA_HOST` |
| `acoustid.py` | fingerprint + parse; `fpcalc` from config (`FPCALC` / bundle `Contents/Helpers/fpcalc`) | `/opt/homebrew` fallback as last resort only |
| `shazam.py` | `parse_shazam`; call bundled helper or `songrec` if present | `~/local_tools/.../shazam-venv` |
| `music_repair.write_file_tags` + `_write_id3_frames` | owned `.mp3` / `.m4a` / `.flac` only | Music.app `set_track_fields` |
| `music_genre.clean_genre` | `EDM, X` → `X`, House compounds, Accapella spelling | AppleScript genre writes, `--xml` rekordbox patch |
| `riff_repair.is_id3_headed` / `is_riff` | detect corrupt WAV; **never write ID3 on WAV/AIFF** (`RIFF_NO_ID3`) | Terrarum `--source`, Music.app relink |

Cache: `~/Library/Caches/CrateID/lookup.json` (or next to the folder as `.crateid-cache.json` if the user prefers portable). User-Agent: `CrateID/0.1 (https://github.com/ixamal/ix)` — MusicBrainz requires a real UA; today's `ix-crate/0.2 (https://github.com/ixamal/ix)` is the template.

### Tag write rules (from `music_repair.py`)

- Write: `.mp3`, `.m4a`, `.flac`.
- Never: `.m4p` (FairPlay), `.stem.m4a` (NI stem atom), `.wav` / `.aiff` / `.aif` (EasyID3 prepends `ID3` where `RIFF`/`FORM` belongs — that is how `riff-repair` was born).
- Dry-run default. `--execute` / UI Apply is the only writer.

### CLI

```text
crateid scan  <folder>     # dry-run JSON + table; default
crateid apply <folder>     # write tags from last scan (or rescan)
crateid undo  <folder>     # restore from the undo log
crateid --strict | --aggressive
crateid --shazam           # opt-in unofficial recognizer
crateid --offline          # filename + tags only
```

Exit 0 on success, 2 on safety errors (same as crate CLI). Scan writes `~/Library/Application Support/CrateID/scans/<utc>.json` plus a copy next to the folder if writable.

### UI

1. Drop a folder (or click Open).
2. Table: file, current artist/album/title/genre, proposed, **source** (`filename`, `tags`, `acoustid`, `itunes+deezer`, `musicbrainz`, `shazam`), **confidence** (see below).
3. Uncheck rows to skip. Unidentified rows stay grey, not proposed.
4. Apply: backup tags → write → undo log.
5. Undo: restore from that log.

Progress: one row at a time (rate limits are 1.1 s MusicBrainz, 0.35 s catalogs, 0.4 s AcoustID, 1.6 s Shazam). No Aqua HUD from `stems`; a Qt progress bar is enough.

### Confidence (crate does not have a single score today)

| Source | Score to show |
| --- | --- |
| `itunes+deezer` dual agree | high |
| AcoustID `score` ≥ 0.85 + duration match | high (`acoustid.py` `MIN_SCORE` is 0.55; treat 0.55–0.85 as medium) |
| iTunes or Deezer with `duration_match` | medium-high |
| MusicBrainz `score` ≥ 80 + known artist | medium (album fill) |
| filename / tags | local (not a catalog hit) |
| Shazam | medium, labeled unofficial |

### Backup + undo (new; crate reports are not an undo log)

Before each write, snapshot the fields we will change (`artist`, `album`, `title`, `genre`, `albumartist`) into `~/Library/Application Support/CrateID/undo/<scan-id>.json`. Undo writes those values back. If the file changed on disk since Apply, refuse and say so.

Do not copy whole audio files. Tag snapshots are enough.

---

## Product 2 — Crate Bridge (OSS now; optional $5–10 signed build later)

Playlist membership across Music.app / Traktor NML / rekordbox.xml, plus drive path remap after files move.

Owner analogue: `crates.py` + `xml_io.py` + the `remaps[]` that `music-organize` hands to [music_migration](https://github.com/ixamal/music_migration). CRATER / Mixed In Key / STEMIT crates stay owner-only.

### Extract into `crate_core`

| Piece | Take | Parameterize |
| --- | --- | --- |
| `PathIndex` (path + hardlink inode) | as-is | none |
| `load_nml_playlists` / `load_xml_playlists` / `plan_membership` | as-is | skip lists (`STEMIT`, `_LOOPS`, smart Music playlists) become config |
| `ingest_xml_collection` / `ingest_nml_collection` | Location rows for files on disk; skip `.m4p`; never a stub | `VOLUME` (today `"Macintosh HD"`) |
| `apply_xml` / `apply_nml` | membership only; cues/energy/comments/grids stay on existing rows | dest folder names (`MUSIC` / `TRAKTOR`) |
| `xml_io.write_tree` | temp + `os.replace` (live `ElementTree.write` truncates first) | none |
| sibling backup | `crates.py` already copies `*.crates.bak` before write | timestamped backups in `~/Library/Application Support/CrateBridge/backups/` |
| `parse_rb_location` / `_traktor_dir_file` / `_rb_location` | path ↔ XML | none |
| Music.app dump / `apply_music` | optional adapter | requires Music.app open + Apple Events entitlement |

Quit checks stay: refuse `--execute` to xml if Rekordbox is running, to nml if Traktor is running (`crates.main`).

### Path remap (the music_migration slice)

`music-organize` already emits `remaps[]` `{from, to}`. Crate Bridge v1 ships a first-party remap so a USB → `~/Music` move does not require the sibling repo:

```text
cratebridge remap --nml <collection.nml> --from /Volumes/Old --to ~/Music
cratebridge remap --xml <rekordbox.xml>  --from /Volumes/Old --to ~/Music
cratebridge remap --map remaps.json      # music-organize report
```

Rewrite Traktor `LOCATION DIR/FILE/VOLUME` and rekordbox `TRACK Location`. Dry-run prints the count. Execute uses `write_tree` + backup. Do not rewrite cues.

Detect Traktor / Rekordbox paths by glob, do not hard-code `Traktor 4.5.1`. Prompt if several collections exist.

### CLI

```text
cratebridge scan  --from music|nml|xml --to music|nml|xml --playlist NAME
cratebridge scan  --from nml --to xml --all
cratebridge apply <scan-id>
cratebridge undo  <scan-id>          # restore the .bak
cratebridge remap --xml|--nml --from ROOT --to ROOT
```

`--no-ingest` keeps the old skip-only behavior.

### UI

1. Pick source and dest (three radio pairs). Browse to `collection.nml` / `rekordbox.xml`. Music.app source requires the app open.
2. Playlist checklist (from `load_*_playlists`). Protected `STEMIT` hidden.
3. Preview table: playlist, matched, ingest, skip (missing / `.m4p`).
4. Apply → backup → write. Banner: reload Rekordbox xml (`<>`); Don't ask again + No on tag overwrite.
5. Second tab: path remap (old root / new root, or drop a `remaps.json`).

### Paid signed build (later)

Same Apache-2.0 / GPL-combined source. The $5–10 is notarization + Sparkle + support, not a feature gate. Unsigned GitHub builds stay free. Do not ship a closed binary (see mutagen).

Out of v1: CRATER, STEMIT factory, Mixed In Key, favorites, `music-dupes` / `music-replicants` (those are Music.app row deletes — dangerous in a stranger's library). Genre cleanup can ride along as an optional checkbox later (`clean_genre` is already pure).

---

## UI toolkit — recommend PySide6

| | PySide6 (Qt) | SwiftUI shell + bundled CLI |
| --- | --- | --- |
| Time to first `.app` | one language; drop folder → table is a weekend | two languages + JSON IPC |
| Reuse | `crate_core` in-process | CLI only; every table row is a subprocess or a daemon |
| Native look | good enough; not App Store candy | best |
| ShazamKit | needs a tiny Swift helper later | natural |
| Notarization | Python + Qt dylibs need extra entitlements | cleaner hardened runtime |
| Drag and drop | `QListWidget` / `QTableView` | native |

**Choose PySide6 for v1.** The work is Python (mutagen, urllib, ElementTree, fpcalc subprocess). A SwiftUI shell still has to ship CPython for the CLI, so you pay the Python-bundle cost twice and split the UI.

Revisit SwiftUI only if we add official ShazamKit or want an App Store build. Then the Swift app calls `crateid` / `cratebridge` over stdio JSONL, same commands as above.

LGPL note: PySide6 / Qt are LGPL-3.0. Dynamic link, ship Qt dylibs, point users at Qt source. Same pattern as bundled `fpcalc`.

---

## Packaging and release

### Bundle tool — PyInstaller, not py2app

- **PyInstaller** is what a GitHub Actions `macos-14` runner will actually produce week after week. One spec per app, `onedir` `.app`.
- **py2app** is the older Mac-native choice and fine as a spike, but it lags Python 3.12 and fights Qt webengine/plugins. Do not start there.
- Pin **CPython 3.12** in the bundle. `crate/pyproject.toml` is `>=3.11`; `shazamio-core` already dies on Homebrew 3.14.

Layout inside `Crate ID.app`:

```
Contents/MacOS/Crate ID          # GUI
Contents/MacOS/crateid           # CLI (same binary, argv[0] or a symlink)
Contents/Helpers/fpcalc          # Chromaprint, LGPL, separate process
Contents/Resources/...
```

CLI on PATH: a post-install note to symlink `/usr/local/bin/crateid`, or a "Install command-line tool" menu. Do not write to `/usr/bin`.

### fpcalc

Chromaprint `fpcalc` is LGPL. Call it as a **separate binary** (already how `acoustid.fingerprint` works: `subprocess.check_output([binary, "-json", path])`). Ship the arm64 (and later universal) binary under `Contents/Helpers/`. Do not statically link libchromaprint into Python. Users can replace the helper.

### Disk image

`create-dmg` (or `dmgbuild`) → `Crate-ID-0.1.0-arm64.dmg` with Applications shortcut. Same for Crate Bridge.

### Signing and notarization

1. Developer ID Application certificate (not Apple Development).
2. `codesign --deep --force --options runtime --entitlements ... --sign "Developer ID Application: …" Crate\ ID.app`
3. Hardened runtime. Python/Qt typically need:
   - `com.apple.security.cs.allow-unsigned-executable-memory`
   - `com.apple.security.cs.disable-library-validation` only if a bundled dylib still unsigned (prefer signing everything)
4. Crate Bridge Music.app: `com.apple.security.automation.apple-events` + `NSAppleEventsUsageDescription`.
5. Folder access: the user dropped it; use security-scoped bookmarks if we keep the last folder across launches.
6. `xcrun notarytool submit Crate-ID.dmg --keychain-profile crate-notary --wait`
7. `xcrun stapler staple Crate-ID.dmg` (and the `.app` if distributed naked).

Secrets stay in GitHub Actions (base64 cert + password, team id, notary Apple ID or App Store Connect API key). Never commit `.p12` or `notarytool` profiles. `docs/security.md` already bans tokens in git.

### Sparkle

Sparkle 2, EdDSA. `appcast.xml` on GitHub Releases (or a static Pages URL). Apps check on launch, download the next signed dmg. Keep a kill-switch in the appcast.

### CI

There is **no** `.github/workflows` in this repo today. Add `macos-14` (Apple Silicon) jobs:

1. `test-packages` — pytest for `crate_core` / crateid / cratebridge (no codesign).
2. `build-dmg` on tag `crateid-v*` / `cratebridge-v*` — PyInstaller, sign, notary, staple, upload Release assets.
3. Keep existing crate unittests on the Ubuntu runner if/when we add one; they must not require the Mac bundle.

Unsigned draft artifacts on PRs are optional; notarized dmgs only on tags.

### Updates and money

GitHub Releases are the store. README badge: Sponsors + Ko-fi. Crate ID stays free. Crate Bridge OSS zip stays free; notarized dmg can later ask $5–10 (Gumroad / Ko-fi shop) with the same tag.

---

## Licensing

| Dependency | License | App rule |
| --- | --- | --- |
| This repo | Apache-2.0 | keep |
| mutagen (`crate/pyproject.toml`) | **GPL-2.0-or-later** | A binary that includes mutagen is a GPL combined work (treat as GPL-3.0). OSS + paid *notarized convenience* is fine. A **closed** paid build is not, unless mutagen is replaced. Do not close Crate Bridge. |
| Chromaprint `fpcalc` | LGPL | separate helper binary |
| PySide6 / Qt | LGPL-3.0 | dynamic Qt dylibs |
| shazamio | unofficial Shazam HTTP | **off by default**, Settings checkbox, first-run warning that this is not an Apple API and can break. Do not put it in the default cascade. |
| ShazamKit | Apple | later, Mac-only, official; Swift helper. Not v1. |
| AcoustID | non-commercial public key | today's `ACOUSTID_CLIENT = "v8pQ6oyB"` is the public client id (`acoustid.py`). Register an application at acoustid.org. Ship with `ACOUSTID_API_KEY` from env / `~/Library/Application Support/CrateID/config.toml`. Never submit fingerprints (existing comment: "Never submit fingerprints. Never Discogs."). |
| MusicBrainz | live service | 1 req/s (`MB_GAP = 1.1`). Descriptive User-Agent with URL. Cache hits. |
| iTunes Search / Deezer | public HTTP | `CATALOG_GAP = 0.35`. Fail soft. |
| Essentia | **AGPL** | do not use, do not vendor, do not "just for BPM". |
| Ollama | local | omit from apps. |

NOTICE file in each `.app` / dmg: Apache-2.0, GPL-2.0+ mutagen, LGPL Qt, LGPL Chromaprint, MusicBrainz / AcoustID terms.

Python 3.12 + shazamio stay an optional extra (`[project.optional-dependencies] shazam` already exists). The app extra is a checkbox, not a pip extra the user sees.

---

## Milestones (weekends)

Rough, one person, no factory / CRATER work in the same weekend.

| | Weekend | Done when |
| --- | --- | --- |
| **0** | This doc + PR | review |
| **1** | `packages/crate_core`: identify + lookup(strict) + tag write + cache injection. Copy tests. No GUI. | `crateid scan testdata/` prints current vs proposed |
| **2** | AcoustID + bundled `fpcalc` lookup. Config-driven API key. | aggressive scan names a silent file |
| **3** | `crateid` CLI (`scan` / `apply` / `undo`) + PySide6 drop-folder table | Apply + Undo on a 20-track folder |
| **4** | PyInstaller `.app`, unsigned dmg, Helpers/fpcalc | double-click on a clean Mac (no Homebrew) |
| **5** | Developer ID, hardened runtime, notarytool, staple, GitHub Release | Gatekeeper-clean dmg |
| **6** | `crate_core` playlist PathIndex + xml/nml apply + remap | `cratebridge scan --from nml --to xml` on a fixture |
| **7** | Crate Bridge UI + Music.app optional adapter | drop nml + xml, preview, apply, Rekordbox `<>` reminder |
| **8** | Sparkle + tag workflow + Sponsors/Ko-fi blurb in README | second signed build updates the first |
| **9** (optional) | Shazam opt-in **or** ShazamKit spike; paid Bridge dmg | checkbox works; unofficial stays off by default |

Weekends 1–5 are Crate ID. 6–8 are Crate Bridge. Slip Shazam without slipping the dmg.

---

## Checklist

### Do not

- [ ] Edit `crate/ix_crate` for this project (no shared import until a later, explicit shim).
- [ ] Hard-code `~/Music`, `~/local_tools`, `/Users/…`, Terrarum, `Traktor 4.5.1`, `Macintosh HD`.
- [ ] Require Music.app for Crate ID.
- [ ] Mutagen-write `.wav` / `.aiff` / `.stem.m4a` / `.m4p`.
- [ ] Discogs, Essentia, Ollama-in-the-app, fingerprint submit.
- [ ] Enable Shazam by default.
- [ ] Ship the AcoustID public client id as the production key.
- [ ] Truncate `rekordbox.xml` / `collection.nml` in place (`write_tree` only).
- [ ] Rewrite cues / energy / Mixed In Key fields.
- [ ] Put `.p12`, notary passwords, or `.env` in git.
- [ ] Close-source a mutagen-linked binary.

### Crate ID v1

- [ ] `packages/crate_core` identify / catalog / MusicBrainz / AcoustID / tag write.
- [ ] Injected cache, UA, rate limits, `fpcalc` path.
- [ ] CLI `scan` / `apply` / `undo`.
- [ ] PySide6 drop folder → table (current / proposed / source / confidence).
- [ ] Tag snapshot undo log.
- [ ] PyInstaller `.app` + `fpcalc` helper + create-dmg.
- [ ] Signed, notarized, stapled GitHub Release.
- [ ] NOTICE + in-app licenses.

### Crate Bridge v1

- [ ] PathIndex + playlist load/apply from `crates.py` logic.
- [ ] Configurable NML/XML paths and volume name.
- [ ] Remap old root → new root (and `remaps.json`).
- [ ] Dry-run default; Rekordbox/Traktor running = refuse write.
- [ ] Backup then `write_tree`.
- [ ] UI: source/dest, playlist list, ingest counts, remap tab.
- [ ] Same sign/notary/Sparkle pipeline.
- [ ] Paid dmg only after legal pass on mutagen (keep source identical).

### Later

- [ ] Optional `crate/ix_crate` import of `crate_core` (one cascade, two UIs).
- [ ] ShazamKit helper.
- [ ] Universal binary (arm64 + x86_64) if Intel still matters.
- [ ] Genre-clean checkbox; never a silent library rewrite.

---

## Relation to the owner's toolkit

| Owner command | Product |
| --- | --- |
| `music-fix` / `lookup.resolve` / `identify` | Crate ID (files only) |
| `crates` | Crate Bridge membership |
| `music-organize` remaps + music_migration | Crate Bridge remap tab |
| `riff-repair` WAV lesson | Crate ID write filter |
| `music-genre.clean_genre` | optional later |
| `crater`, `stemit`, `mixed-in-crate`, `favorites`, `music-dupes` | stay in `crate/` |

If a booth-only idea (STEMIT HUD, AppleScript locate `!`, Mixed In Key) is tempting in the GUI, it is the wrong app.
