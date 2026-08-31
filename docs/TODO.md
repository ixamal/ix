# TODO

Hit these in order. Stop on the first open item. Detail and constraints live in `docs/notes.md`. Off-repo tools and library paths stay off git.

Last update: 2026-08-31 (phone-session docs on main — review on Mac).

## Review on Mac

Merged onto `main` 2026-08-31. `git pull` in `~/github/ixamal/ix`. Not a crate execute step. First numbered open item is still **5**.

- [ ] [#1](https://github.com/ixamal/ix/pull/1) — NI/Maschine idea parked. BlackHole **16ch**, then Traktor A/B/C → Maschine sampler → S88. `docs/notes.md`.
- [ ] [#2](https://github.com/ixamal/ix/pull/2) — Music.app `set genre` specimen (TODO **4a**). `docs/examples/music-set-genre.applescript`. Do not run.

## Crate

- [x] 1. ATGR in (ReCK, DJCU2, Mixed in Key). Traktor collection migrated into Rekordbox.
- [x] 1a. Unknown Album, mashups, and Inbox emptied. Unidentified leftovers: `Compilations/Mashups/Miscellaneous/`.
- [x] 1b. `stems_audio/Unknown Artist/` gone. 6 stale NML rows rematched (unicode + Queen mix). 5 ScreenRecording role WAVs no longer on disk. Apple Music `Unknown Artist` untouched.
- [x] 1c. Traktor `collection.nml` remapped (27,564 live / 1,302 unmatched). Playlist keys repaired (100). Backup: `collection.nml.bak`.
- [x] 2. DJCU2 Traktor → Rekordbox (2026-08-30). Playlists/folders landed. Process: `docs/djcu2.md`. Site: [atgr.nl](https://atgr.nl/).
- [x] 3. Path-stable. 4,908 shared live owned files: Traktor and Rekordbox same path on 4,901 (4,164 stems + 634 Music.app). Music.app locations match on a 4-track owned sample (Charles Spencer, Ella, Portishead, RY X). 7 leftover hoist-path mismatches, not the sample crate.

## Tagging

- [x] 4. Genre pass. Files: 9 Accapella → `Acapella`; 11,031 `EDM, …` → `House` / `Techno` / … (disk leftover 0). Music.app library then AppleScript-updated (12 Accapella + 11,719 compounds; leftover 0; 14 `Acapella`). Beatport 1.7.0 dead; Discogs probe unsafe (Electronic + one Hip Hop miss). Sync Library Off. Detail: `docs/onetagger.md`.
- [x] 4a. Learned: Music.app does not re-read file tags. Cloud-download rows are library entries. File write + AppleScript both required. Specimen for review: `docs/examples/music-set-genre.applescript` ([#2](https://github.com/ixamal/ix/pull/2)).
- [ ] 5. Fill **empty** genre/subgenre from Beatport / Traxsource / Discogs when Beatport v4 works. Never overwrite ReCK/MiK Camelot/key, BPM, comments, or cues. Do not Discogs-blast the old `EDM, …` set.
- [ ] 6. Ollama tag reviewer only: `127.0.0.1:11434`, JSON/CSV proposals for untagged tracks, human approve, then allowlisted write. Crate ID already uses `qwen2.5:7b`; do not use the coder as the musicologist.
- [x] 7. Beets is not the library of record. If used at all: `copy: no`, `move: no`, `write: no`, DB under `~/local_tools/beets`. Gemini `item.write()` plugin rejected.

## Floor / Engine

- [ ] 8. ix Floor: Rekordbox/Traktor OSC on `127.0.0.1:9000` (`/rekordbox/bpm`, `/fader`, `/beat_phase`) into UE. No ID3, no library convert.
- [ ] 8a. Enable UE OSC plugin. Listen `127.0.0.1:9000`.
- [ ] 8b. Niagara Grid 3D Gas/Smoke. Record 15s sim cache.
- [ ] 8c. Bind `/rekordbox/bpm` and `/rekordbox/fader` to cache Explicit Time / density.

## NI / Maschine (after Floor; crate is stable)

Do not start these while Floor (8) is open. Detail: `docs/notes.md`. Execution: [ixamal/blackhole](https://github.com/ixamal/blackhole). Parked via [#1](https://github.com/ixamal/ix/pull/1) (now on main).

- [ ] 9. Port the working BlackHole **2ch Channel D** graph onto **16ch**. Prove tone, Traktor A, and S88-only-on-D. Then Traktor A/B/C → Maschine sampler → S88 keys. KK out. Link is clock only.
- [ ] 10. Python conversion of Traktor / Native Instruments material to WAV or AIFF for Maschine + S88 if file samples are needed. Off-repo under `~/local_tools`.
- [ ] 11. Try Traktor Kontrol S8 pads driving S88 sample slots (Maschine / Komplete Kontrol S88). MIDI/bridge experiment after 9.
