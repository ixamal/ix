# DJCU2 — Traktor ↔ Rekordbox

[ATGR](https://atgr.nl/) (Mixmaster G) makes **DJ Conversion Utility Two**. Site: [atgr.nl](https://atgr.nl/). It is the crate bridge on this Mac after identity repair. ix does not replace it.

DJCU2 moves playlists, cues, loops, and beatgrids between Traktor, Rekordbox, Serato, Engine, VirtualDJ, and djay. Confirmed on this machine 2026-08-30: full Traktor → Rekordbox after the `stems_audio` dump. It works. We do not reimplement that convert.

## Process

STEMIT crates, titles, and `STEMIT/Genres` live in Traktor NML. Crate does **not** rewrite `rekordbox.xml` for this pass. DJCU2 is the bridge.

1. Reopen Traktor. Confirm All Tracks, **STEMIT** Mixes / Stems / Acapellas / Instrumentals, and **STEMIT/Genres** (one folder per genre, four role playlists each). Mix / stem / vocals / instrumental are four files, not copies. Leftover same-title copies can wait.
2. Quit Traktor and Rekordbox.
3. **Export** the collection from Traktor (File → Export Collection, complete NML). **Uncheck** export audio files. A copy of the live `collection.nml` is still the original and DJCU2 will warn — that is fine; use the export you just made.
4. Run **DJ Conversion Utility Two**: From Traktor → To Rekordbox. Include playlists and folders. Do not copy audio.
5. Snapshot the live DBs into `databases/` on this Mac (gitignored). See `databases/README.md`.
6. Reopen Rekordbox. Confirm STEMIT + Genres folders landed, cues/grids survived, paths still under `~/Music`.

Do not overwrite ReCK / Mixed in Key key, BPM, comments, or cues in a later tag pass. Do not Discogs-blast.

## Also from ATGR

- **ReCK** — writes Mixed in Key into Rekordbox.
- **RCT** — Rekordbox collection repair / relocate.

Buy and docs: [atgr.nl](https://atgr.nl/).
