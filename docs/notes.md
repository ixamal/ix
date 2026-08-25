# Working notes (do not execute from this file)

Parking lot for crate, tagging, and hardware ideas. Ordered checklist: `docs/TODO.md`. Agents: read both, then stop unless David asks to act. Off-repo tools and library paths stay off git.

Last update: 2026-08-24 (David to gym; catalog only).

## Crate status

- ATGR installed (ReCK, DJCU2, related Mixmaster G tools).
- Traktor collection migrated into Rekordbox.
- **Bug / follow-up:** Traktor folders/playlists expected in Rekordbox did not show up. Come back later. Do not re-run conversion or rewrite the crate until we inspect DJCU2 folder/playlist mapping.
- Target integration: Traktor + Rekordbox + Music.app, with Mixed in Key for key/energy/cues.

## Tagging (queued, not started)

Do this only after the Rekordbox folder question is understood and a small crate is path-stable.

1. **OneTagger** off-repo, in place, tiny sample folder of *owned files* (not Apple Music streams).
2. Fill empty genre/subgenre from Beatport / Traxsource / Discogs.
3. Never overwrite ReCK/MiK fields: Camelot/key, BPM, comments, cues.
4. **Ollama** second pass as reviewer only: `127.0.0.1:11434`, JSON/CSV proposals for untagged tracks, human approve, then allowlisted write.
5. Do not use `qwen2.5-coder:7b` as the musicologist. Pull a general model later if needed.
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
- Commit these notes unless David asks.
