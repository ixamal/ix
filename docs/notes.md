# Working notes (do not execute from this file)

Parking lot for crate, tagging, and hardware ideas. Ordered checklist: `docs/TODO.md`. Agents: read both, then stop unless David asks to act. Off-repo tools and library paths stay off git.

Last update: 2026-09-01. This Mac pulled phone PRs 1–4 (`1f420de`). Crate + genre closed. Next doable: Floor 8. Item 5 blocked (Beatport). 5b parked.

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

1. Floor / Elysium (`docs/TODO.md` item 8). UE OSC `127.0.0.1:9000` → Niagara 15s cache.
2. Item 5 stays blocked until Beatport v4. Do not Discogs-blast the old `EDM, …` set.
3. Item 5b stays parked. Do not run until David asks.

```bash
PYTHONPATH=crate python3 -m ix_crate unknown-album
PYTHONPATH=crate python3 -m ix_crate outliers
PYTHONPATH=crate python3 -m ix_crate mashups
```

## Tagging

Path-stable crate done 2026-08-30. Accapella + `EDM, …` genre pass done 2026-08-30 (files + Music.app AppleScript). Step log: `docs/onetagger.md`.

1. **OneTagger** 1.7.0 Beatport is dead (API v4). Discogs is unsafe for the old Apple `EDM, …` compounds (flattened to Electronic; one compilation → Hip Hop).
2. Fill **empty** genre/subgenre from stores when Beatport works again.
2a. Music.app genre is the library DB, not the file. After file writes, AppleScript `set genre` (one track at a time). Specimen: `docs/examples/music-set-genre.applescript` (do not run). Sync Library is Off — keep it off for the DJ crate.
2b. **Embed-while-processing (TODO 5b, idea, not started).** Python module in the processing pipeline (`crate/` or `~/local_tools`, not a live OneTagger blast). While a track is already being handled, stamp the file with **any available** field: artist, album, title, genre, duration, BPM, key, comments, cue points. Lookups from the same class of web databases OneTagger uses (Beatport / Traxsource / Discogs — Beatport v4 still dead on 1.7.0). Fill empties only for ReCK/MiK key, BPM, comments, cues. Do not Discogs-blast the old `EDM, …` set.
    - Owned `.mp3` / `.wav` / `.m4a` only. Never `.m4p`. Never Apple Music streams.
    - **Never mutagen `save()` on `.stem.m4a`.** That strips the NI `udta` stem atom and Traktor loses four decks. Stamp the mix / vocals / instrumental siblings in the file tags.
    - **STEM sidecar:** because the `.stem.m4a` cannot take a safe tag write, store the same metadata as JSON **in parallel with the audio tree** — sibling `{name}.stem.json` next to `{name}.stem.m4a`, same `Artist/Album/` folders. Sidecars stay on disk next to the music, never in public git. Move/rename with the family so the JSON does not orphan.
    - Cue points: only write a format Traktor or Rekordbox actually reads on mix/role files. For STEMs, put cues in the JSON sidecar. Do not invent a cue atom Traktor ignores. Collection cues stay in NML / `master.db` unless David asks otherwise.
    - After file writes, Music.app still needs AppleScript (4a). Dry-run + report first. `--execute` only when David asks.
3. Never overwrite ReCK/MiK fields: Camelot/key, BPM, comments, cues.
4. **Ollama** second pass as reviewer only: `127.0.0.1:11434`, JSON/CSV proposals for untagged tracks, human approve, then allowlisted write.
5. Do not use `qwen2.5-coder:7b` as the musicologist. Crate ID uses `qwen2.5:7b`. Tag reviewer is still a later allowlisted write.
6. **Beets** is not the library of record. If used at all: `copy: no`, `move: no`, `write: no`, DB under `~/local_tools/beets`. Default `beet import` copies files and would break DJCU2/ReCK/Music.app paths. Gemini’s `item.write()` plugin is rejected.

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
