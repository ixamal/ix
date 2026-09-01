# TODO

Hit these in order. Stop on the first **doable** open item. Detail: `docs/notes.md`. Off-repo tools and library paths stay off git.

Last update: 2026-09-01. This Mac is on `1f420de` (phone PRs [#1](https://github.com/ixamal/ix/pull/1)–[#4](https://github.com/ixamal/ix/pull/4) pulled). Item **5** is blocked. Next doable work is **8** (Floor / Elysium).

## Now

Crate is path-stable. Accapella + `EDM, …` genre closed (files + Music.app). Sync Library Off. Phone ideas from 2026-08-31 are on `main`.

**Next session:** Floor — Rekordbox/Traktor OSC on `127.0.0.1:9000` into UE Niagara (8 → 8a → 8b → 8c).

Do not start 5, 5b, 6, or 9 unless David asks. Beatport 1.7.0 is still dead.

## Crate (done)

- [x] 1. ATGR in (ReCK, DJCU2, Mixed in Key). Traktor collection migrated into Rekordbox.
- [x] 1a. Unknown Album, mashups, Inbox emptied. Leftovers: `Compilations/Mashups/Miscellaneous/`.
- [x] 1b. `stems_audio/Unknown Artist/` gone. 6 stale NML rows rematched. 5 ScreenRecording WAVs gone.
- [x] 1c. Traktor `collection.nml` remapped (27,564 live / 1,302 unmatched). Playlist keys repaired (100).
- [x] 2. DJCU2 Traktor → Rekordbox (2026-08-30). Process: `docs/djcu2.md`. Site: [atgr.nl](https://atgr.nl/).
- [x] 3. Path-stable. 4,908 shared live owned files; Traktor and Rekordbox same path on 4,901.

## Tagging

- [x] 4. Genre pass. 9 Accapella + 11,031 `EDM, …` on disk; then 11,731 Music.app library rows. Leftover `EDM*`: 0. 14 `Acapella`. Sync Library Off. `docs/onetagger.md`.
- [x] 4a. Music.app does not re-read file tags. Specimen (do not run): `docs/examples/music-set-genre.applescript`.
- [ ] 5. **Blocked.** Empty genre from Beatport / Traxsource / Discogs when Beatport v4 exists. Do not Discogs-blast the old `EDM, …` set. Do not overwrite ReCK/MiK key, BPM, comments, cues.
- [ ] 5b. **Parked.** Embed available metadata while processing. Never mutagen-write `.stem.m4a` — STEM JSON sidecar beside the file. Dry-run first. `docs/notes.md`.
- [ ] 6. **Later.** Ollama tag reviewer only (`qwen2.5:7b` on `127.0.0.1:11434`). Human approve, then allowlisted write. Not the coder.
- [x] 7. Beets is not the library of record.

## Floor / Elysium (do this)

- [ ] 8. Rekordbox/Traktor OSC on `127.0.0.1:9000` (`/rekordbox/bpm`, `/fader`, `/beat_phase`) into UE. No ID3, no library convert.
- [ ] 8a. Enable UE OSC plugin. Listen `127.0.0.1:9000`.
- [ ] 8b. Niagara Grid 3D Gas/Smoke. Record 15s sim cache.
- [ ] 8c. Bind `/rekordbox/bpm` and `/rekordbox/fader` to cache Explicit Time / density.

## NI / Maschine (after Floor)

Parked in [ixamal/blackhole](https://github.com/ixamal/blackhole). Do not start while Floor is open.

- [ ] 9. Port BlackHole **2ch Channel D** onto **16ch**. Then Traktor A/B/C → Maschine sampler → S88.
- [ ] 10. Convert NI/Traktor material to WAV or AIFF only if file samples are needed. `~/local_tools`.
- [ ] 11. S8 pads → S88 sample slots. After 9.
