# Working notes (do not execute from this file)

Parking lot for crate, tagging, and hardware ideas. Ordered checklist: `docs/TODO.md`. Agents: read both, then stop unless David asks to act. Off-repo tools and library paths stay off git.

Last update: 2026-09-08. STEMIT night: Industry Stems artists (31), disk dedupe **286** (32), Beatport TITLEs **229**, Finder `(2)` copies **920** (34), genre crates **53** (35). Mix / stem / vocals / instrumental stay four files. Leftover same-title copies in Traktor are still there — next drop after DJCU2 unless David asks first. **Next on the Mac:** reopen Traktor, confirm STEMIT + Genres, then DJCU2 (`docs/djcu2.md`). Alternative stems 1–3 (TODO 17) unless David names another playlist. Floor **10** parked. Toolkit: README. How/why: `docs/crate.md`.

## Crate status

- ATGR installed (ReCK, DJCU2, Mixed in Key).
- [ixamal/stems](https://github.com/ixamal/stems) processed `~/Music/stems_audio`.
- Identity tool lives in this repo: `crate/`, `docs/crate.md`.
- Cascade: filename → tags → iTunes/Deezer → MusicBrainz → Ollama `qwen2.5:7b` on `127.0.0.1:11434` → `Compilations/Mashups/Miscellaneous/`.
- Mashups: `Compilations/Mashups/{Artist}/`. Leftover clips and one-word names: `Miscellaneous`.
- Ollama music ID uses `qwen2.5:7b` (pulled 2026-08-30). `qwen2.5-coder:7b` stays off this job.

Reports (off git): `~/local_tools/crate/reports/`. Cache: `~/local_tools/crate/lookup-cache.json`.

Traktor (2026-08-30): NML remapped, then [ATGR DJCU2](https://atgr.nl/) converted the collection to Rekordbox. It works. ix does not reimplement that bridge. Snapshots: `databases/` (off git). Steps: `docs/djcu2.md`.

### Resume next

1. **Remap leftover:** Rekordbox XML **539** + master.db **38**. Traktor live NML remapped **561** (backup `collection.nml.pre-organize-606-20260906T142655`). Leftover junk with identity: **51** added to Music.app (library **21,875**).
2. **STEMIT** (31–35): reopen Traktor. Confirm Industry Stems artists, thinner crates, `STEMIT/Genres/<Genre>/{Mixes,Stems,Acapellas,Instrumentals}`. Leftover same-title copies still show — they are not the four role files. Then DJCU2 (`docs/djcu2.md`). Do not rewrite `rekordbox.xml`. Alternative stems 1–3 (TODO 17) unless David names another playlist.
2a. Sanity later: `stemit --genres` / `--drop-copies` / `--dedupe` (dry-run first). Quit Traktor for `--execute`.
3. Floor **10** parked until David asks.
4. Items 5 / 5b / 6 stay omitted. Do not Discogs-blast. Targeted one-album Discogs from a screenshot is OK (TODO 22 / `docs/crate.md`).

```bash
PYTHONPATH=crate python3 -m ix_crate unknown-album
PYTHONPATH=crate python3 -m ix_crate outliers
PYTHONPATH=crate python3 -m ix_crate mashups
PYTHONPATH=crate python3 -m ix_crate music-dupes
PYTHONPATH=crate python3 -m ix_crate music-dupes --execute
PYTHONPATH=crate python3 -m ix_crate music-repair
PYTHONPATH=crate python3 -m ix_crate music-repair --execute
PYTHONPATH=crate python3 -m ix_crate music-genre
PYTHONPATH=crate python3 -m ix_crate music-replicants
PYTHONPATH=crate python3 -m ix_crate music-cull
PYTHONPATH=crate python3 -m ix_crate music-organize
PYTHONPATH=crate python3 -m ix_crate music-organize --playlist Fix
PYTHONPATH=crate python3 -m ix_crate riff-repair
PYTHONPATH=crate python3 -m ix_crate music-fix --playlist Fix
PYTHONPATH=crate python3 -m ix_crate music-fix --playlist Fix --execute
PYTHONPATH=crate python3 -m ix_crate stemit --playlist "Never Forget 50th v01"
PYTHONPATH=crate python3 -m ix_crate stemit --playlist "Never Forget 50th v01" --execute
PYTHONPATH=crate python3 -m ix_crate stemit --fix-role-titles
PYTHONPATH=crate python3 -m ix_crate stemit --fix-role-titles --execute
PYTHONPATH=crate python3 -m ix_crate stemit --fix-role-titles --nml --execute
PYTHONPATH=crate python3 -m ix_crate stemit --fix-industry-artists
PYTHONPATH=crate python3 -m ix_crate stemit --fix-titles
PYTHONPATH=crate python3 -m ix_crate stemit --drop-copies
PYTHONPATH=crate python3 -m ix_crate stemit --genres
PYTHONPATH=crate python3 -m ix_crate stemit --dedupe
PYTHONPATH=crate python3 -m ix_crate stemit --sync-playlists
```

## Tagging

Path-stable crate done 2026-08-30. Accapella + `EDM, …` genre pass done 2026-08-30 (files + Music.app AppleScript). Step log: `docs/onetagger.md`.

1. **OneTagger** 1.7.0 Beatport is dead (API v4). Discogs is unsafe for the old Apple `EDM, …` compounds (flattened to Electronic; one compilation → Hip Hop).
2. **TODO 5 omitted (2026-09-01).** Not viable on this Mac. David is happy enough with the TODO 4 catalog to play in Rekordbox. Do not compile community PRs unless he asks.
    - [OneTagger 1.7.0](https://github.com/Marekkon5/onetagger/releases/tag/1.7.0) — last official Mac release, 2023-08-03. Beatport scrape in that build is dead.
    - [Beatport API v4](https://api.beatport.com/v4/docs/) — current catalog API (OAuth). 1.7.0 does not speak it.
    - [Issue #486](https://github.com/Marekkon5/onetagger/issues/486) — Beatport/Traxsource/Juno break after the v3→v4 cut.
    - [Issue #518](https://github.com/Marekkon5/onetagger/issues/518) / [#520](https://github.com/Marekkon5/onetagger/issues/520) — `__NEXT_DATA__` scrape gone.
    - [PR #526](https://github.com/Marekkon5/onetagger/pull/526) (rosgr100) — v4 OAuth + catalog search. Open since 2026-05, last activity 2026-06, **not merged**. Linux CLI testers say it works. No official Mac asset.
    - [PR #523](https://github.com/Marekkon5/onetagger/pull/523) — earlier Beatport v4 search attempt after `__NEXT_DATA__` removal.
2a. Music.app genre is the library DB, not the file. After file writes, AppleScript `set genre` (one track at a time). Specimen: `docs/examples/music-set-genre.applescript` (do not run). Sync Library is Off — keep it off for the DJ crate. Copy-on-add is On. **Keep Music Media folder organized** is Off — `music-organize` is the mover, so the artist-root crate is not hoisted into `Music/`. New files land in `Media.localized/Music/Artist/Album/`; the existing crate stays at `Media.localized/Artist/`. Never recreate `Media.localized/Music` as a symlink to `.` (breaks drag-and-drop). Details: `docs/crate.md`.
2b. **TODO 5b omitted (2026-09-01).** Same blocker as 5: embed-while-processing was store lookups (Beatport / Traxsource / Discogs). Those stores are not viable here. If this ever reopens: owned `.mp3` / `.wav` / `.m4a` only; never `.m4p`; never mutagen `save()` on `.stem.m4a` (strips NI stem atom); sidecar `{name}.stem.json` beside the file, not in git.
3. Never overwrite ReCK/MiK fields: Camelot/key, BPM, comments, cues.
4. **TODO 6 omitted (2026-09-01).** Ollama (`qwen2.5:7b` on `127.0.0.1:11434`) was reviewer-after-stores, not a catalog. 5 never runs, so 6 would invent genres. Reopen only if Rekordbox leftovers bother David: JSON/CSV proposals, human approve, allowlisted write. Never the coder.
5. Do not use `qwen2.5-coder:7b` as the musicologist. Crate ID already uses `qwen2.5:7b`.
6. **Beets** is not the library of record. If used at all: `copy: no`, `move: no`, `write: no`, DB under `~/local_tools/beets`. Default `beet import` copies files and would break DJCU2/ReCK/Music.app paths. Gemini’s `item.write()` plugin is rejected. Crate fingerprinting is AcoustID (`fpcalc`) plus Shazam (`shazamio`; optional `songrec`). `music-fix --library-va` writes tags in place and does not move Media.localized.

ix Floor stays live OSC (`/rekordbox/bpm`, `/fader`, `/beat_phase`). It does not convert libraries or write ID3.

## NI / Maschine (idea, crate stable, not started)

Crate is path-stable (TODO 3) and the genre pass is closed (TODO 4). The old “wait until the crate is stable” gate is lifted. Still do not wire this until David asks. Execution lives in [ixamal/blackhole](https://github.com/ixamal/blackhole), not this repo.

Working rig (2026-08-22): S88 keys (Light Guide) into Komplete Kontrol or Maschine, down **BlackHole 2ch**, into Traktor Channel D, out the S8 fader. KK and Maschine share one D fader. Leave Maschine Input off BlackHole (loop). Leave S8 unchecked in Maschine MIDI. Close KK when Maschine needs the S88.

**Next session (blackhole, in this order):**

1. Port the working 2ch Channel D graph onto **BlackHole 16ch**. Prove tone, Traktor A, and S88-only-on-D still behave. Commit there only after this works.
2. Then tap Traktor **A/B/C into the Maschine sampler**, play pads on the **S88**. KK out — KK does not sample live decks. Ableton Link is clock, not audio. Open question: Internal Traktor may not offer three independent deck outs; 16ch alone does not invent them. Do not record the master into BlackHole while Channel D is up (feedback).
3. Convert Traktor / NI material to WAV or AIFF for Maschine + S88 only if file samples are needed. Off-repo under `~/local_tools`.
4. **Idea to try:** can **Traktor Kontrol S8** pads drive **S88** sample slots (Maschine / Komplete Kontrol S88)? MIDI/bridge after 1–2.

Keep converters and MIDI maps in `~/local_tools`, not in this public repo. Rekordbox / FLX10 stays later — keep RB shut during this work.

## Parked in siblings (not this repo)

- [ixamal/blackhole](https://github.com/ixamal/blackhole) — 2ch Channel D works. Next: 16ch, then A/B/C → Maschine → S88.
- [ixamal/ix_bangers](https://github.com/ixamal/ix_bangers) — Bangers MCP catalog (stems, Music, Rekordbox, Traktor). Dry mode until David says commit. Not native Traktor.
- [ixamal/stems](https://github.com/ixamal/stems) — factory idle after the first `stems_audio` pass. Parked there: dump the crate to JSON + a spreadsheet webpage. Not now.

## Do not do until asked

- Re-run DJCU2 on the whole library unless David asks.
- Run OneTagger Discogs against the whole library (wrong compilation matches; flattens to Electronic).
- Run OneTagger against Apple Music streams (`.m4p`).
- Turn on Music.app **Sync Library** on this DJ crate (still matches/replaces local files; not a hybrid keep-local mode).
- Convert NI/Traktor audio to WAV/AIFF.
- Port BlackHole 2ch → 16ch, or tap Traktor A/B/C into Maschine.
- MIDI-map S8 pads to S88 samples.
- Run Bangers writes (dry catalog only; [ixamal/ix_bangers](https://github.com/ixamal/ix_bangers)).
- Re-run crate `--execute` on a live tree unless David asks.
- Run the embed-while-processing stamp (TODO 5b) on a live crate unless David asks.
