# Working notes (do not execute from this file)

Parking lot for crate, tagging, and hardware ideas. Ordered checklist: `docs/TODO.md`. Agents: read both, then stop unless David asks to act. Off-repo tools and library paths stay off git.

Last update: 2026-08-30. Unknown Album, mashups, and Inbox **executed**. `_outliers` is gone.

## Crate status

- ATGR installed (ReCK, DJCU2, Mixed in Key).
- [ixamal/stems](https://github.com/ixamal/stems) processed `~/Music/stems_audio`.
- Identity tool lives in this repo: `crate/`, `docs/crate.md`.
- Cascade: filename → tags → iTunes/Deezer → MusicBrainz → Ollama `qwen2.5:7b` on `127.0.0.1:11434` → `Compilations/Mashups/Miscellaneous/`.
- Mashups: `Compilations/Mashups/{Artist}/`. Leftover clips and one-word names: `Miscellaneous`.
- Ollama music ID uses `qwen2.5:7b` (pulled 2026-08-30). `qwen2.5-coder:7b` stays off this job.

Reports (off git): `~/local_tools/crate/reports/`. Cache: `~/local_tools/crate/lookup-cache.json`.

### Resume next

1. Remaining `Unknown Artist/`, then the rest of `stems_audio`.
2. Rebuild Traktor via music_migration.
3. DJCU2 → Rekordbox. Do not reconvert until the tree is clean.

```bash
PYTHONPATH=crate python3 -m ix_crate unknown-album
PYTHONPATH=crate python3 -m ix_crate outliers
PYTHONPATH=crate python3 -m ix_crate mashups
```

## Tagging (queued, not started)

Do this only after the Rekordbox folder question is understood and a small crate is path-stable.

1. **OneTagger** off-repo, in place, tiny sample folder of *owned files* (not Apple Music streams).
2. Fill empty genre/subgenre from Beatport / Traxsource / Discogs.
3. Never overwrite ReCK/MiK fields: Camelot/key, BPM, comments, cues.
4. **Ollama** second pass as reviewer only: `127.0.0.1:11434`, JSON/CSV proposals for untagged tracks, human approve, then allowlisted write.
5. Do not use `qwen2.5-coder:7b` as the musicologist. Crate ID uses `qwen2.5:7b`. Tag reviewer is still a later allowlisted write.
6. **Beets** is not the library of record. If used at all: `copy: no`, `move: no`, `write: no`, DB under `~/local_tools/beets`. Default `beet import` copies files and would break DJCU2/ReCK/Music.app paths. Gemini’s `item.write()` plugin is rejected.

ix Floor stays live OSC (`/rekordbox/bpm`, `/fader`, `/beat_phase`). It does not convert libraries or write ID3.

## NI / Maschine (idea, not started)

- Look at Python automation or libraries to convert Traktor / Native Instruments material to WAV or AIFF for **Maschine** with the **S88**.
- **Idea to try:** can **Traktor Kontrol S8** pads drive **S88** sample slots (collected samples on Maschine / Komplete Kontrol S88)? Hardware MIDI/bridge experiment. Do not wire this until the crate is stable.
- Keep any converters and MIDI maps in `~/local_tools`, not in this public repo.

## Do not do until asked

- Debug missing Rekordbox folders from the Traktor migrate.
- Install or run OneTagger / Beets against the live crate.
- Convert NI/Traktor audio to WAV/AIFF.
- MIDI-map S8 pads to S88 samples.
- Re-run crate `--execute` on a live tree unless David asks.
