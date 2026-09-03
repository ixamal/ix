# Crate identity repair

`stems` writes STEM siblings. [music_migration](https://github.com/ixamal/music_migration) remaps Traktor/Rekordbox after files move. **This package** repairs identity in `~/Music/stems_audio`.

Audio never enters git. Reports and lookup cache: `~/local_tools/crate/`.

## Cascade (every family)

1. **Filename** — `Artist - Title` or `Artist - Album - Title`, junk stripped. `Artist _ Title` and `Artist | Title` only when the left side is ≤4 words.
2. **Tags** — mix-file tags only; ignore role-file `instrumental` / `vocals`.
3. **iTunes + Deezer** — title + duration (or both catalogs agree). Mashups, clips, and mixes ≥20 min stay out.
4. **MusicBrainz** — fill album only when artist is already known.
5. **Ollama** — `127.0.0.1:11434` JSON. Default `qwen2.5:7b`. Coder models are skipped. Artist must appear in the filename.
6. **`Compilations/Mashups/Miscellaneous/`** — leftover bucket after lookup. Never `Unknown Artist` / `Unknown Album`. Scan still starts from `_outliers/Inbox/`.

No skips. Families (mix + stem + vocals/instrumental) always move together.

Mashups: `Compilations/Mashups/{Artist}/`. Also moves `{Artist}/Mashups/` and placeholder albums (`Unknown Album`, `_ album title goes here _`). Artist description is the parent folder name.

## Commands

```bash
cd ~/github/ixamal/ix
cd crate && PYTHONPATH=. python3 -m unittest tests.test_identify tests.test_stemit -q
cd ~/github/ixamal/ix
PYTHONPATH=crate python3 -m ix_crate unknown-album            # dry-run + lookups
PYTHONPATH=crate python3 -m ix_crate unknown-album --offline  # filename/tags only
PYTHONPATH=crate python3 -m ix_crate unknown-album --execute  # after you read the report
PYTHONPATH=crate python3 -m ix_crate outliers                 # re-ID _outliers/Inbox (dry-run)
PYTHONPATH=crate python3 -m ix_crate outliers --execute       # after you read the outliers report
PYTHONPATH=crate python3 -m ix_crate mashups                  # Compilations/Mashups dry-run
PYTHONPATH=crate python3 -m ix_crate mashups --execute
PYTHONPATH=crate python3 -m ix_crate music-dupes              # Music.app same-file rows (dry-run + HUD)
PYTHONPATH=crate python3 -m ix_crate music-dupes --execute    # drop extra library rows; file stays
PYTHONPATH=crate python3 -m ix_crate music-repair             # Locate ! rows (dry-run + HUD)
PYTHONPATH=crate python3 -m ix_crate music-repair --execute   # set location + fill empty identity/genre
PYTHONPATH=crate python3 -m ix_crate music-reconcile          # relink ! rows from the iTunes XML (dry-run)
PYTHONPATH=crate python3 -m ix_crate music-reconcile --execute
PYTHONPATH=crate python3 -m ix_crate music-fix                # playlist Fix identity (dry-run + HUD)
PYTHONPATH=crate python3 -m ix_crate music-fix --execute      # write file tags + Music.app artist/album/genre
PYTHONPATH=crate python3 -m ix_crate music-fix --library-va   # library Various Artists (dry-run)
PYTHONPATH=crate python3 -m ix_crate music-fix --library-va --execute
PYTHONPATH=crate python3 -m ix_crate stemit --playlist "Never Forget 50th v01"
PYTHONPATH=crate python3 -m ix_crate stemit --playlist "Never Forget 50th v01" --execute
```

## After this dump

Unknown Album, mashups, and Inbox are executed. `_outliers` is gone. Unidentified leftovers: `Compilations/Mashups/Miscellaneous/`.

1. Traktor remapped. DJCU2 confirmed. Path-stable crate confirmed (TODO 3).
2. Genre pass done (TODO 4): owned `Media.localized` tags + Music.app library. See `docs/onetagger.md`.

Never *move* Apple Music `Media.localized`. In-place genre on owned `.mp3`/`.m4a` was TODO 4 only. Never commit `/Users/<name>/` paths.

## Music.app media folder

Copy-on-add is the default and it works. Drag Beatport / Traxsource files onto Music.app.

The library media folder is `~/Music/Music/Media.localized`. The DJ crate already lives as **Artist / Album** folders at that root (Traktor and Rekordbox point there). New copies from Music.app go into a real subdirectory:

`Media.localized/Music/Artist/Album/file`

Do **not** turn `Media.localized/Music` into a symlink to `.`. That leftover iTunes loop made drag-and-drop fail with **Attempting to copy to the disk “Data” failed. A duplicate file name was specified.** (“Data” is the APFS user volume, not a second disk.) Replaced with a real `Music/` folder 2026-09-03; Traxsource drag-and-drop confirmed.

Removing the loop had a cost that was not caught the same day. 7,110 rows had been written while it existed, so they record `Media.localized/Music/Artist/...` for a file that actually sits at `Media.localized/Artist/...`. The loop made both spellings resolve; a real folder does not. 5,368 rows went to **!** immediately. `music-reconcile` repaired them by pointing each row at the real path, so the library no longer depends on the loop existing.

Leave **Sync Library** Off. Do not hoist new `Music/` files up onto the artist-root crate. Do not delete `Music/` to “flatten” the library. `music-repair` indexes both trees and skips `Music/` as an artist name.

## music-reconcile

`music-repair` matches a dead row by artist/title against what is on disk, which only lands when the title is unique. `music-reconcile` starts from `Media.localized/iTunes Music Library.xml` instead: it records **persistent ID → path**, and the live library still uses those same IDs. That turns a guess into an exact per-row lookup.

For each row Music.app reports as `missing value`, in order:

1. the path the XML recorded, if that file is still there
2. the same path with the `Music/` container removed (the symlink fallout above)
3. the same path rebased onto a backup `Media.localized` root (`--external`)
4. artist/title match over a wider external tree (`--external-scan`)

A candidate is only used when no live row already holds it, so a relink can never mint a duplicate. Rows whose file is already claimed are reported as `duplicate_rows` and left for `music-dupes`.

Two things about reading the library that cost a day:

- Read `location` in **bulk** (`location of file tracks i thru j`). The per-track form inside a repeat fails to coerce on this library and reports every row as dead — that is where the bogus "14,127 missing" first came from.
- Relinking **reorders** `library playlist 1`, so a position captured during the scan goes stale mid-run. Each write re-checks the persistent ID at that index and skips on mismatch, and `--passes` re-scans until it converges. The first single-pass run relinked 7,580 and skipped 5,536 purely from drift.

```bash
PYTHONPATH=crate python3 -m ix_crate music-reconcile            # dry-run
PYTHONPATH=crate python3 -m ix_crate music-reconcile --execute  # relink, re-scanning until stable
PYTHONPATH=crate python3 -m ix_crate music-reconcile \
  --external     "/Volumes/<drive>/MIGRATION_MASTER/Music/Music/Media.localized" \
  --external-scan "/Volumes/<drive>/MIGRATION_MASTER/Music"
```

2026-09-03: **8,748 → 21,850** rows holding a file (13,102 relinked, 7,748 at their recorded path, 5,368 hoisted out of `Music/`). 991 left: 103 duplicate rows, 888 with no file anywhere local.

Relinking to a removable volume is left as a dry-run on purpose — those rows go **!** again the moment the drive unmounts. Copy in first, then relink.

## STEMIT

Name for the local stem factory job: Music.app playlist → hardlink the mix into `~/Music/stems_audio/Artist/Album/` → [ixamal/stems](https://github.com/ixamal/stems) `py.exec.separate` as the RUNBOOK does (`PATH` = stems `.venv/bin` first, then that venv’s `python -m py.exec.separate`). Mel vocals/instrumental + `{name}.stem.m4a`. Aqua HUD is `py.utils.progress`. Homebrew Python 3.12 `.venv` in the stems repo. ~3.8 min/track. `audio-separator` lives in that venv — do not call the factory with system PATH.

Never write Apple Music. Never mutagen-write `.stem.m4a`. Never stem **Acapella**. Skip if that dest already has `{name}.stem.m4a`. Dry-run unless `--execute`. Queue m3u + reports: `~/local_tools/crate/` (off git). Add the new siblings in Traktor / Rekordbox when David wants — do not hand-edit NML.

The mix is a **hardlink**, not a copy: one set of bytes, two paths (Apple Music + `stems_audio`). Deleting the `stems_audio` name never deletes the Apple Music file.

First run, 2026-09-03 — Music playlist `Never Forget 50th v01`, **21 tracks**: 21 `.stem.m4a`, 20 full Rekordbox pairs, 42/42 factory writes, **0 fail**, 1.50 GB, **78 min** (3.7 min/track, ~38 s per audio minute). Lords Of Acid *Undress and Possess* hit `we found none` — Mel found no separable vocal, so **both** pair files dropped and the container still muxed. That is correct: the mix already is the instrumental.

The shell can look like it ran for hours after the batch ends — the Aqua HUD stays open until **Close**. Read `summary.wall_s_total` in the run JSON for real time, not shell elapsed.

`music-dupes` only deletes extra Music.app *rows* that share one existing file. It does not unlink audio. If a delete would trash the file, it restores from Trash and stops.

`music-repair` relinks Songs rows with no file (the Locate / ! mark) to a unique match under Media.localized. It does not move Apple Music files. Empty artist/album/title uses the crate cascade. Empty genre uses iTunes only.

`music-fix` fills identity on a playlist (default `Fix`). Default is **aggressive**: Chromaprint/AcoustID, duration-matched iTunes or Deezer, MusicBrainz length match, then **Shazam** (`shazamio` in `~/local_tools/crate/shazam-venv`; optional `songrec`) for cuts catalogs missed. Unidentified leftovers stay as they are — crate does **not** salvage them as Various Artists. `--library-va` scans the library artist instead of a playlist. `--strict` is dual-catalog only. Gaps only unless `--all`. Cream Live album stays. Dump folders become `Singles` when a real artist is found. Hits write album artist and clear the compilation flag so Apple Music files them under the artist, not Various Artists. In-place tags on owned audio; no Media.localized moves. The crate CLI never Discogs-blasts. Beets is not used (`docs/notes.md`).

## Screenshot compilations

Batch fingerprinting (TODO 21) cannot fix a mix CD that already has *wrong* artists (every cut tagged as the DJ). When David sends a screenshot of one album:

1. Identify **that** release on Discogs / iTunes / Wikipedia. One compilation at a time. Do not walk the library.
2. Strip leading `01 ` / `02 ` from **titles**. Mix-CD `01 Artist` in the **artist** field is the same junk — keep real numbered names (16 Bit Lolitas, 28 East Boyz, 51 Days, 68 Beats, 95 North).
3. Write the liner/Discogs track artist. Album artist is the DJ or series brand (Tenaglia, Farina, Lazy Dog), not Various Artists and not a guess from another screenshot. Compilation **off** so the album stays under that album artist.
4. Unify name variants (`Vol. 2` vs `Volume 2`, `[Disc 1]` vs `(Disc 1)`) onto one album + disc numbers. Drop extra Music.app **rows** only — never unlink audio, never move `Media.localized`.
5. Prefer the row that still has a file. If the keeper is a Locate `!`, re-add the rip (`Music add POSIX file`) and delete the empty row. AppleScript `POSIX path of location` often lies on these files; `location as text` (HFS) is the check.
6. After a large write, Music.app may need a quit/reopen before Next follows disc/track order. Shuffle in the transport is independent of tags.

Reports and lookup cache stay in `~/local_tools/crate/` (off git).
