# TODO

Hit these in order. Stop on the first **doable** open item. Detail: `docs/notes.md`. Off-repo tools and library paths stay off git.

Last update: 2026-09-01. Music Locate/! rows (18) relinked. **Next: Alternative stems, tracks 1–3 only** (validate). Never stem Acapella. Floor **10** parked.

## Now

Crate is path-stable. `EDM, …` and Accapella are done (files + Music.app). Sync Library Off.

**Next:** Alternative stems, tracks **1–3 only**, so David can validate the HUD + siblings. Skip if that Artist/Album/Title already has `{name}.stem.m4a` in `~/Music/stems_audio`. Never write Apple Music. Never stem **Acapella**. Floor 10 when David asks.

Do not start 11 unless David asks. Do not farm 35k to the cloud.

## Crate (done)

- [x] 1. ATGR in (ReCK, DJCU2, Mixed in Key). Traktor collection migrated into Rekordbox.
- [x] 1a. Unknown Album, mashups, Inbox emptied. Leftovers: `Compilations/Mashups/Miscellaneous/`.
- [x] 1b. `stems_audio/Unknown Artist/` gone. 6 stale NML rows rematched. 5 ScreenRecording WAVs gone.
- [x] 1c. Traktor `collection.nml` remapped (27,564 live / 1,302 unmatched). Playlist keys repaired (100).
- [x] 2. DJCU2 Traktor → Rekordbox (2026-08-30). Process: `docs/djcu2.md`. Site: [atgr.nl](https://atgr.nl/).
- [x] 3. Path-stable. 4,908 shared live owned files; Traktor and Rekordbox same path on 4,901.
- [x] 16. **Music.app same-file rows.** 625 files had two Songs entries on the same path (Show in Finder → same file). Dropped 625 extra library rows. Files stayed (23,632 → 23,007 file tracks). `PYTHONPATH=crate python3 -m ix_crate music-dupes`. Aqua HUD via stems `py.utils.progress`.
- [x] 18. **Music.app Locate / ! rows.** Relinked 375 unique disk matches (`music-repair`). 16 Bit Lolitas from the screenshot included. 260 unmatched (duplicate copies, truncated mix-CD names, or no file). Identity/genre fill only on gaps (crate cascade + iTunes genre). Did not move Media.localized. Did not Discogs.

## Tagging

- [x] 4. `EDM, …` prefix + Accapella. 11,031 files + 11,731 Music.app rows. Leftover `EDM*`: 0. 14 `Acapella`. Incomplete for comma leftovers — see **8** and **9**. `docs/onetagger.md`.
- [x] 4a. Music.app does not re-read file tags. Same two-layer write applies to 8 and 9. Specimen (do not run): `docs/examples/music-set-genre.applescript`.
- [x] 5. **Omitted (not viable).** Beatport via OneTagger 1.7.0. [PR #526](https://github.com/Marekkon5/onetagger/pull/526) unmerged. Links: `docs/notes.md`.
- [x] 5b. **Omitted (not viable).** Embed-while-processing needed the same stores as 5. STEM rule if reopened: never mutagen-write `.stem.m4a`.
- [x] 6. **Omitted.** Ollama was reviewer-after-stores. Not a catalog.
- [x] 7. Beets is not the library of record.
- [x] 8. **`House, …` comma compounds.** 1,135 owned files + 1,301 Music.app rows. `House, Deep` → Deep House (699), Tech → Tech House (268), Progressive → Progressive House (136), plus Funk/Soul/Disco, Minimal/Deep Tech, Melodic, Indie/Nu Disco, Electro, Latin, Garage, STEMS, doubled labels. Music.app leftover `House,`: **0**. Disk leftover: **0**.
- [x] 9. **Merge Hip Hop spellings.** `Hip-Hop` → `Hip Hop` on files. Music.app: one leftover — Freddie Joachim *Rain Drops* (file permission / likely stream). Left `Hip Hop / House` (1). Did not fold `Hip-Hop/Rap` or `Hip Hop / R&B`.

## Stems (genre batches, local factory)

Factory: [ixamal/stems](https://github.com/ixamal/stems) `py.exec.separate`. Dest is `~/Music/stems_audio` (hardlink the mix first). Skip if that Artist/Album/Title already has a `.stem.m4a`. ~3.8 min/track on this Mac.

- [x] 14. **Acapella — do not stem.** Sources already *are* the vocal. Let It Go and I Get Deep already have `.stem.m4a`. Music.app extras have no local file.
- [x] 15. **Afro House.** Dialed In already had stem + pair. Local factory wrote Roots, Koma Kobache, Iris (hardlink mix in `stems_audio`, then Mel pair + `.stem.m4a`). Never wrote Media.localized.
- [ ] 17. **Alternative, tracks 1–3 only.** Validate HUD + pair + `.stem.m4a` before the rest of the genre. Skip existing `stems_audio` Artist/Album/Title. Hardlink mix first. Never stem Acapella.

## Floor / Elysium (parked)

- [ ] 10. Rekordbox/Traktor OSC on `127.0.0.1:9000` (`/rekordbox/bpm`, `/fader`, `/beat_phase`) into UE. No ID3, no library convert.
- [ ] 10a. Enable UE OSC plugin. Listen `127.0.0.1:9000`.
- [ ] 10b. Niagara Grid 3D Gas/Smoke. Record 15s sim cache.
- [ ] 10c. Bind `/rekordbox/bpm` and `/rekordbox/fader` to cache Explicit Time / density.

## NI / Maschine (after Floor)

Parked in [ixamal/blackhole](https://github.com/ixamal/blackhole). Do not start while Floor is open.

- [ ] 11. Port BlackHole **2ch Channel D** onto **16ch**. Then Traktor A/B/C → Maschine sampler → S88.
- [ ] 12. Convert NI/Traktor material to WAV or AIFF only if file samples are needed. `~/local_tools`.
- [ ] 13. S8 pads → S88 sample slots. After 11.
