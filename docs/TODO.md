# TODO

Hit these in order. Stop on the first open item. Detail and constraints live in `docs/notes.md`. Off-repo tools and library paths stay off git.

Last update: 2026-08-25.

## Crate

- [x] 1. ATGR in (ReCK, DJCU2, Mixed in Key). Traktor collection migrated into Rekordbox. ix does not own this crate.
- [ ] 2. Inspect why Traktor folders/playlists did not appear in Rekordbox. DJCU2 folder mapping. Do not reconvert until we know why.
- [ ] 3. Confirm a small crate is path-stable across Music.app, Rekordbox, and Traktor (same files). Gate for everything below.

## Tagging

- [ ] 4. OneTagger off-repo, in place, on a tiny folder of owned files (not Apple Music streams, not the whole library).
- [ ] 5. Fill empty genre/subgenre from Beatport / Traxsource / Discogs. Never overwrite ReCK/MiK Camelot/key, BPM, comments, or cues.
- [ ] 6. Ollama reviewer only: `127.0.0.1:11434`, JSON/CSV proposals for untagged tracks, human approve, then allowlisted write. Do not use `qwen2.5-coder:7b` as the musicologist.
- [x] 7. Beets is not the library of record. If used at all: `copy: no`, `move: no`, `write: no`, DB under `~/local_tools/beets`. Gemini `item.write()` plugin rejected.

## Floor / Engine

- [ ] 8. ix Floor: Rekordbox/Traktor OSC on `127.0.0.1:9000` (`/rekordbox/bpm`, `/fader`, `/beat_phase`) into UE. No ID3, no library convert.
- [ ] 8a. Enable UE OSC plugin. Listen `127.0.0.1:9000`.
- [ ] 8b. Niagara Grid 3D Gas/Smoke. Record 15s sim cache.
- [ ] 8c. Bind `/rekordbox/bpm` and `/rekordbox/fader` to cache Explicit Time / density.

## NI / Maschine (after crate is stable)

- [ ] 9. Python conversion of Traktor / Native Instruments material to WAV or AIFF for Maschine + S88. Off-repo under `~/local_tools`.
- [ ] 10. Try Traktor Kontrol S8 pads driving S88 sample slots (Maschine / Komplete Kontrol S88). MIDI/bridge experiment after 9.
