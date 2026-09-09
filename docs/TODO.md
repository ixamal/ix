# TODO

Hit these in order. Stop on the first **doable** open item. Detail: `docs/notes.md`. Off-repo tools and library paths stay off git.

Last update: 2026-09-08. Playlist **Fix** identity closed (19 + 20). Various Artists fingerprint pass done (21). Screenshot compilations closed (22). **STEMIT** shipped and first playlist is done (23). `EDM, …` recurrence + replicants closed (24). Ghosts culled (25). **music-organize** shipped (26) and second folder pass applied. STEMIT crates shipped (27). Industry Stems + disk copies + genre crates (31–35). Floor **10** parked.

## Now

Crate is path-stable. Music.app is playable. Sync Library Off. Copy-on-add works. STEMIT proved end to end. Disk names: **17** placeholders + **606** artist-root folder moves.

**Next:** Reopen Traktor — confirm STEMIT + **Genres**, then DJCU2 (`docs/djcu2.md`). Leftover same-title copies in STEMIT stay for a later pass (roles are four files). Alternative stems, tracks **1–3 only** (TODO 17), or another playlist through **STEMIT** when David names one. Never write Apple Music from the factory. Never stem **Acapella**. Floor 10 when David asks.

Do not start 11 unless David asks. Do not farm 35k to the cloud. Do not Discogs-blast.

## Crate (done)

- [x] 1. ATGR in (ReCK, DJCU2, Mixed in Key). Traktor collection migrated into Rekordbox.
- [x] 1a. Unknown Album, mashups, Inbox emptied. Leftovers: `Compilations/Mashups/Miscellaneous/`.
- [x] 1b. `stems_audio/Unknown Artist/` gone. 6 stale NML rows rematched. 5 ScreenRecording WAVs gone.
- [x] 1c. Traktor `collection.nml` remapped (27,564 live / 1,302 unmatched). Playlist keys repaired (100).
- [x] 2. DJCU2 Traktor → Rekordbox (2026-08-30). Process: `docs/djcu2.md`. Site: [atgr.nl](https://atgr.nl/).
- [x] 3. Path-stable. 4,908 shared live owned files; Traktor and Rekordbox same path on 4,901.
- [x] 16. **Music.app same-file rows.** 625 files had two Songs entries on the same path (Show in Finder → same file). Dropped 625 extra library rows. Files stayed (23,632 → 23,007 file tracks). `PYTHONPATH=crate python3 -m ix_crate music-dupes`. Aqua HUD via stems `py.utils.progress`.
- [x] 18. **Music.app Locate / ! rows.** Relinked 375 unique disk matches (`music-repair`). 16 Bit Lolitas from the screenshot included. 260 unmatched (duplicate copies, truncated mix-CD names, or no file). Identity/genre fill only on gaps (crate cascade + iTunes genre). Did not move Media.localized. Did not Discogs.
- [x] 19. **Music.app playlist Fix.** 685 file tracks. Tagged **188** (filename 125, iTunes+Deezer 58, Ollama 5). **497** left unidentified (`Track 01`, Cream Live, mix-CD names with no unique catalog match). Dump albums → `Singles` when artist known. Cream Live kept. WAV mutagen abort replayed. `PYTHONPATH=crate python3 -m ix_crate music-fix --playlist Fix --execute`. No Discogs. Did not move Media.localized.
- [x] 20. **Fix leftovers — heavy pass.** 497 remaining gaps tagged. iTunes 126, Deezer 20, MusicBrainz 21, dual catalog 3, Various Artists salvage 327. Playlist Fix now has **0** empty artists. AcoustID ran on every gap (mix-CD rips mostly unlinked in the fingerprint DB). Cream Live kept. No Discogs. Did not move Media.localized.
- [x] 21. **Various Artists cleanup.** AcoustID + Shazam (`shazamio` in `~/local_tools/crate/shazam-venv`, Python 3.12). No Beets import. 263 tagged (237 Shazam, 18 MusicBrainz, 6 iTunes/Deezer, 2 tags). 75 unidentified left as VA. Hits write artist, album artist, clear compilation. `music-fix --library-va --execute`. Report `~/local_tools/crate/reports/music-fix-20260903T040145Z.json`.
- [x] 22. **Screenshot compilations (one album at a time).** David sends a Music.app shot; agent looks up **that** Discogs/iTunes release only (not a library blast). Write per-track artists, DJ/compiler as album artist, compilation **off**, genre House unless the shot says otherwise. Strip `01 Title` prefixes. Unify duplicate album-name variants; drop extra Music.app **rows** only. Keep the file-backed row (or re-add the rip if the keeper was a `!`). How/why: `docs/crate.md` (Screenshot compilations). Done this night: mix-CD numbered **artist** prefixes (keep 16 Bit Lolitas / 28 East Boyz / 51 Days / 68 Beats / 95 North); Mix This Pussy; GU **010 Athens** discs 1–2 (album artist Danny Tenaglia); Mushroom Jazz 7 order + two duration mislabels; Lazy Dog + Volume 2 (Ben Watt & Jay Hannan, 53 extra rows dropped, 3 `!` relinked). Music.app may need a quit/reopen after a big write; Shuffle is independent of tag order.

- [x] 23. **STEMIT + Music.app copy-on-add.** Drag-and-drop into Music.app failed with *“Attempting to copy to the disk ‘Data’ failed. A duplicate file name was specified.”* Cause: `Media.localized/Music` was a leftover iTunes **symlink to `.`**, so every copy landed on an existing path. Replaced with a real folder; Beatport + Traxsource drag-and-drop confirmed. New copies live at `Media.localized/Music/Artist/Album/`; the old crate stays at `Media.localized/Artist/`. `music-repair` now skips `Music/` as an artist name. Then built **STEMIT** (`ix_crate stemit`): Music.app playlist → hardlink mix into `stems_audio` → stems `py.exec.separate`. First run **Never Forget 50th v01**: 21/21 tracks, 42/42 factory writes, 0 fail, 1.50 GB, 78 min (3.7 min/track). Lords Of Acid *Undress and Possess* correctly dropped its pair (`we found none` — the mix **is** the instrumental) and still got `.stem.m4a`. All 21 mixes are still hardlinks to Apple Music (no copies, no moves).
- [x] 24. **EDM recurrence + replicants.** Consolidation brought `EDM, …` back (229 rows) and copied already-held tracks in again because iTunes names a second copy `Track 1.m4a`. Terrarum recover brought 66 more. `music-genre` promotes the prefix on files + library (two-layer; leftover `EDM*`: 0). Never mutagen-write `.wav`. `music-replicants` drops extra rows whose files decode to the same audio (476). `music-dupes` dropped 146 same-file extras. `consolidate` now strips the iTunes duplicate marker from title keys. How/why: `docs/crate.md`. README toolkit.
- [x] 25. **Cull remaining `!` / invalid media.** Terrarum search closed. `music-cull` dropped **425** Music.app rows (424 empty location, 1 `.itlp`). **0** corrupt WAV/AIFF. Library **21,824** file tracks, leftover drop **0**. Valid files stayed. How/why: `docs/crate.md`.
- [x] 26. **Disk names from Music.app metadata.** `music-organize` files `Media.localized` as Artist / Album / `NN Title` from the Songs row. Playlist Fix is gone. Compilations stay unless album artist is the DJ; split compilations stay together. `Media.localized/Music/` folder moves are locked (Music.app restores them). `--placeholders-only` executed **17** `Track 01` renames. Second pass: **606** artist-root tracks now under `Music/Artist/Album`; **472** Music-tree files stayed. How/why: `docs/crate.md`.
- [x] 27. **STEMIT crate playlists.** `--sync-playlists` walks `stems_audio` in any state and writes Traktor + Rekordbox **Mixes / Stems / Acapellas / Instrumentals**. 2026-09-06 execute: 8,785 on disk; Traktor +3,904 rows; Rekordbox XML +7,823 rows. Never push acapellas back to Apple Music. Analyze stays in-app.
- [ ] 28. **Role titles (`vocals`).** Disk tags written 2026-09-07. NML patched **4,709** titles (Traktor quit). Reopen Traktor, confirm All Tracks, then **DJCU2** to Rekordbox. Do not rewrite rekordbox.xml. OneTagger Beatport is dead; do not Discogs-blast.
- [x] 29. **Traktor playlist dupes + artwork.** 2026-09-07: dropped **237** duplicate PRIMARYKEY rows (Humid chills 86, stems_audio 94, 2024 Alive 29, …). Copied **3,512** sibling COVERARTIDs (8 broken pointers replaced). Backup `collection.nml.pre-nml-repair-20260907T133704Z`. Mix/stem/vocals are not copies. Reopen Traktor. Then DJCU2.
- [x] 30. **STEMIT copy-twins.** Mixes was listing `.stem (2).m4a` and `vocals (2).wav` next to the real files. Dropped **186** Finder copies after mutagen length + decoded-audio match (WAV/mp3). STEMIT crates rebuilt from disk; numbered `(2)` files are not listed. 889 stem `(2)` files kept on disk (size/head differ — not the same bytes). Reopen Traktor. Then DJCU2.
- [x] 30a. **STEMIT looked empty.** ElementTree `clear()` stripped `TYPE="LIST"` / `UUID`; rewrite also left empty name-only playlist shells first. Traktor shows the first node. Fixed 2026-09-07: four crates Mixes 1403 / Stems 1896 / Acapellas 2032 / Instrumentals 1749, each `TYPE=LIST`. Reopen Traktor.
- [x] 31. **Industry Stems artists + STEMIT crate keepers.** 2026-09-08: **202/209** packs crate-matched (7 remix leftovers still IndustryStems). Patched **808** NML ARTIST rows. Never WAV tags. STEMIT crates rebuilt: one row per identity, **383** extra playlist rows dropped (Stems 125 groups). Files stayed on disk. Specimens: `docs/examples/stemit-industry-artists.py`, `docs/examples/music-set-industry-artist.applescript`. Reopen Traktor. Then DJCU2.
- [x] 32. **STEMIT disk dedupe.** 2026-09-08: **286** copies deleted (197 + 89), **43** empty folders pruned. Unique mashups stayed. Industry Stems WAV packs stayed. Live vs studio (FLA Gun) kept. Google Drive shortcut skipped. STEMIT rebuilt. Reopen Traktor. Then DJCU2.
- [x] 34. **Finder `(2)` copies.** 2026-09-08: deleted **920** disk copies (same title+artist role as the keeper) and dropped missing stems_audio NML rows. Mix/stem/vocals/instrumental stayed four files. Live vs studio stayed. Reopen Traktor. Then DJCU2.
- [x] 35. **STEMIT genre crates.** 2026-09-08: `stemit --genres --execute` cleaned **3844** NML GENRE rows (`EDM, House, Deep` → Deep House) and wrote **53** `STEMIT/Genres/<Genre>/{Mixes,Stems,Acapellas,Instrumentals}` crates from keepers. Re-run anytime. Reopen Traktor. Then DJCU2.

## Tagging

- [x] 4. `EDM, …` prefix + Accapella. 11,031 files + 11,731 Music.app rows. Leftover `EDM*`: 0. 14 `Acapella`. Incomplete for comma leftovers — see **8** and **9**. `docs/onetagger.md`.
- [x] 4a. Music.app does not re-read file tags. Same two-layer write applies to 8 and 9. Specimen (do not run): `docs/examples/music-set-genre.applescript`.
- [x] 5. **Omitted (not viable).** Beatport via OneTagger 1.7.0. [PR #526](https://github.com/Marekkon5/onetagger/pull/526) unmerged. Links: `docs/notes.md`.
- [x] 5b. **Omitted (not viable).** Embed-while-processing needed the same stores as 5. STEM rule if reopened: never mutagen-write `.stem.m4a`.
- [x] 6. **Omitted.** Ollama was reviewer-after-stores. Not a catalog.
- [x] 7. Beets is not the library of record.
- [x] 8. **`House, …` comma compounds.** 1,135 owned files + 1,301 Music.app rows. `House, Deep` → Deep House (699), Tech → Tech House (268), Progressive → Progressive House (136), plus Funk/Soul/Disco, Minimal/Deep Tech, Melodic, Indie/Nu Disco, Electro, Latin, Garage, STEMS, doubled labels. Music.app leftover `House,`: **0**. Disk leftover: **0**.
- [x] 9. **Merge Hip Hop spellings.** `Hip-Hop` → `Hip Hop` on files. Music.app: one leftover — Freddie Joachim *Rain Drops* (file permission / likely stream). Left `Hip Hop / House` (1). Did not fold `Hip-Hop/Rap` or `Hip Hop / R&B`.

## Stems (STEMIT)

**STEMIT** = Music.app playlist → hardlink mix into `~/Music/stems_audio` → [ixamal/stems](https://github.com/ixamal/stems) `py.exec.separate` (HUD: `py.utils.progress`). Skip if that Artist/Album/Title already has a `.stem.m4a`. ~3.8 min/track on this Mac. `PYTHONPATH=crate python3 -m ix_crate stemit --playlist "…"`. How/why: `docs/crate.md`.

- [x] 14. **Acapella — do not stem.** Sources already *are* the vocal. Let It Go and I Get Deep already have `.stem.m4a`. Music.app extras have no local file.
- [x] 15. **Afro House.** Dialed In already had stem + pair. Local factory wrote Roots, Koma Kobache, Iris (hardlink mix in `stems_audio`, then Mel pair + `.stem.m4a`). Never wrote Media.localized.
- [x] 16b. **STEMIT proved.** `Never Forget 50th v01`, 21 tracks: 21 `.stem.m4a`, 20 full Rekordbox pairs, 1 correct pair drop, 0 fail. 78 min. Detail in item 23.
- [ ] 17. **Alternative, tracks 1–3 only.** Same STEMIT path, genre batch instead of a playlist. Skip existing `stems_audio` Artist/Album/Title. Never stem Acapella.

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
