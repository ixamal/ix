# Crate identity repair

`stems` writes STEM siblings. [music_migration](https://github.com/ixamal/music_migration) remaps Traktor/Rekordbox after files move. **This package** started as identity repair in `~/Music/stems_audio` and grew into the Music.app crate toolkit: relink, pull a migration home, promote leftover genres, drop ghosts, un-break WAVs, STEMIT.

Audio never enters git. Reports and lookup cache: `~/local_tools/crate/`. Steal the ideas: README *Crate toolkit*. Do not copy our `/Users` paths.

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
PYTHONPATH=crate python3 -m ix_crate music-genre              # promote 'EDM, X' → 'X' (dry-run)
PYTHONPATH=crate python3 -m ix_crate music-genre --execute    # write file tags + Music.app genre
PYTHONPATH=crate python3 -m ix_crate music-replicants         # same recording, two filenames (dry-run)
PYTHONPATH=crate python3 -m ix_crate music-replicants --execute
PYTHONPATH=crate python3 -m ix_crate music-cull               # drop ! / missing / unreadable rows (dry-run)
PYTHONPATH=crate python3 -m ix_crate music-cull --execute
PYTHONPATH=crate python3 -m ix_crate riff-repair              # restore ID3-headed WAV, drop (2)/(3) twins (dry-run)
PYTHONPATH=crate python3 -m ix_crate riff-repair --execute
PYTHONPATH=crate python3 -m ix_crate consolidate SOURCE       # pull audio back into ~/Music (dry-run + HUD)
PYTHONPATH=crate python3 -m ix_crate consolidate SOURCE --execute
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

2026-09-03: **8,748 → 21,850** rows holding a file (13,102 relinked, 7,748 at their recorded path, 5,368 hoisted out of `Music/`). Then `consolidate` brought the crate back local and a second pass with `--external-scan ~/Music/Music/Media.localized` relinked 291 more.

**22,173 of 22,873 rows now resolve, all under `~/Music`. No row points at `/Volumes`.** After `music-genre` and `music-replicants` (2026-09-04): **22,251** file tracks. After Terrarum recover + `music-cull`: **21,824** file tracks, **0** leftover `!` / unreadable rows. No leftover `EDM,` genre.

Never relink to a removable volume. Those rows go **!** again the moment it unmounts. Copy in first with `consolidate`, then relink against the local tree.

## consolidate

An earlier migration moved audio out of `~` onto Terrarum. That is the root cause of the library rows with no file, and the reason the crate has to be pulled back rather than merely relinked.

`consolidate` walks a source tree, drops what is already held locally, and files the rest under `~/Music` as **Artist / Album**.

**Tags decide the destination, not source paths.** The exFAT copy truncated long filenames and rewrote `/` as `_` (`08 Head Affect _ Afrochrome [Gent.mp3`), so the source layout cannot be trusted, but the tags survived. Untagged audio falls back to the folders around it, ignoring containers that say nothing about who made it (`Desktop`, `Documents`, `Downloads`, `Library`, `CloudStorage`). Separator output named for the role alone (`vocals.wav`) is routed to `stems_audio` keeping its project folder as the album — otherwise thousands of identically named files pile into one directory.

Duplicate test is exact byte size plus normalized title, confirmed by hashing the leading 4MB only when a pair ties. Size alone collides across encodes of the same length, title alone collides across compilations. Both the tag title and the filename title count, because truncation makes them disagree. iTunes names a second copy `Track 1.m4a`; that trailing marker is stripped from the title key so a held track is not copied in again.

Copy only. Sources are never moved or deleted, existing files are never overwritten, a colliding name gets a numbered suffix, and each file lands via a size-checked `.partial`. A run is repeatable and safe to interrupt.

```bash
PYTHONPATH=crate python3 -m ix_crate consolidate "/Volumes/<drive>/<path>" --index-cache ~/local_tools/crate/local-audio-index.json
PYTHONPATH=crate python3 -m ix_crate consolidate "/Volumes/<drive>/<path>" --index-cache ~/local_tools/crate/local-audio-index.json --execute
```

`--index-cache` is worth passing. Reading tags across the whole local library takes about half an hour, and the cache makes it reusable — but **delete it after copying**, or the next run will still believe the new files are absent.

2026-09-03: 26,640 scanned, 790 already held, **22,457 copied (273 GB)**. The run then stopped: Terrarum unmounted mid-copy and the remaining 3,393 all failed on a vanished source. `consolidate` now tells a lost volume apart from one unreadable file and stops on the first rather than reporting one problem 3,393 times.

## music-genre

The 2026-08-30 OneTagger pass (`docs/onetagger.md`) cleared `EDM, …` from the crate. Consolidating the migration drive brought the spelling back on tracks that had never been through that pass.

`music-genre` strips a leading `EDM,` only (`EDM, House` → `House`, `EDM, House, Deep` → `House, Deep`). Slash store spellings (`Funk / Soul / Disco`, `Electronica / Downtempo`) are left alone. Music.app does **not** re-read file tags, so the write is two-layer: mutagen on owned `.mp3` / `.m4a` (never `.m4p` or WAV/AIFF — ID3 prepends and breaks RIFF), then AppleScript `set genre` on the library row. `--passes` re-scans because editing a row can reorder `library playlist 1`. Click off a stale genre selection in the column browser after a run.

```bash
PYTHONPATH=crate python3 -m ix_crate music-genre
PYTHONPATH=crate python3 -m ix_crate music-genre --execute
```

2026-09-04: **229** rows (182 `EDM, House` → `House`, 23 Ambient, 20 Electronica, 4 `House, Deep`). File tags 229, library rows 229, leftover `EDM*`: **0**.

Same day, after the Terrarum recover: **66** more (42 House, 13 Electronica, 9 Ambient, 1 `House, Deep`, 1 `Electronica / Downtempo`). Those copies still wore the old prefix; Music.app showed it when the rows came back. Leftover `EDM*`: **0**.

## music-replicants

`music-dupes` groups rows by path. It cannot see the other shape: two rows, two files, identical audio. iTunes writes a second copy as `Track 1.m4a`, and `consolidate` added more of those until the title key learned the marker.

`music-replicants` groups by artist/album/title, then compares **decoded** audio (ffmpeg mono 22 kHz MD5). Tag bytes on a re-saved `.m4a` differ while the recording does not; a raw-byte test called hundreds of real twins distinct. DRM that will not decode falls back to leading bytes. A group that disagrees is left alone — alternate takes share a title legitimately. Playlist membership wins the keeper so a crate slot is never emptied. Deleting an extra row may bin that row's own file; the kept copy is re-checked after every delete and the run stops if it vanished.

```bash
PYTHONPATH=crate python3 -m ix_crate music-replicants
PYTHONPATH=crate python3 -m ix_crate music-replicants --execute
```

2026-09-04: **476** extra rows dropped (decoded-audio twins) plus **146** same-file extras via `music-dupes`. Remaining same-title groups are different audio (left). The dead `!` rows next to them were later culled.

## music-cull

Terrarum `MIGRATION_MASTER` has been searched. Rows that are still `!` and not on that drive stay off the hunt. `music-cull` drops the Music.app row when the location is empty, the path is not a file, or the file is unreadable (empty, or a WAV/AIFF that no longer starts with RIFF/FORM). Valid files stay. `.m4p` purchases stay even if ffmpeg cannot decode them. Dry-run is the default.

```bash
PYTHONPATH=crate python3 -m ix_crate music-cull
PYTHONPATH=crate python3 -m ix_crate music-cull --execute
```

2026-09-04: **425** rows dropped (424 empty location, 1 leftover `.itlp`). **0** corrupt WAV/AIFF on disk. Library **21,824** file tracks, leftover drop **0**. What is not on Terrarum is a later hunt, not a Music.app ghost.

## riff-repair

`music-fix` / EasyID3 wrote `ID3` onto `.wav` files. That is where `RIFF` belongs, so Music.app and ffmpeg refuse the file (*invalid start code ID3[3]*). `consolidate` then copied the still-valid Terrarum original in as `Track (2).wav` (and later `(3)`) because the bloated corrupt file no longer matched on size.

`riff-repair` walks a folder (default `Media.localized`, recursive), groups `Name.wav` / `Name (2).wav`, keeps the unnumbered name, copies a valid RIFF (local sibling or `--source`) over the corrupt keeper, and deletes extras only when decoded audio matches. Music.app rows that pointed at a deleted `(2)` / `(3)` are relinked to the keeper. Dry-run is the default. The tag writers now skip WAV/AIFF entirely (`RIFF_NO_ID3`).

```bash
PYTHONPATH=crate python3 -m ix_crate riff-repair
PYTHONPATH=crate python3 -m ix_crate riff-repair --execute
```

2026-09-04: library-wide pass on `Media.localized` — **699** `.wav`, all `RIFF`, **0** ID3-headed leftovers, **0** leftover `(2)` / `(3)` groups.

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
