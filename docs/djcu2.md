# DJCU2 — Traktor ↔ Rekordbox

[ATGR](https://atgr.nl/) (Mixmaster G) makes **DJ Conversion Utility Two**. Site: [atgr.nl](https://atgr.nl/). It is the crate bridge on this Mac after identity repair. ix does not replace it.

DJCU2 moves playlists, cues, loops, and beatgrids between Traktor, Rekordbox, Serato, Engine, VirtualDJ, and djay. Confirmed on this machine 2026-08-30: full Traktor → Rekordbox after the `stems_audio` dump. It works. We do not reimplement that convert.

## Process

1. Repair files with `crate/` (`docs/crate.md`). Remap Traktor with [music_migration](https://github.com/ixamal/music_migration).
2. Quit Traktor and Rekordbox.
3. **Export** the collection from Traktor (complete NML). **Uncheck** export audio files. A copy of the live `collection.nml` is still the original and DJCU2 will warn.
4. Run **DJ Conversion Utility Two**: From Traktor → To Rekordbox. Include playlists and folders.
5. Snapshot the live DBs into `databases/` on this Mac (gitignored). See `databases/README.md`.
6. Reopen Rekordbox. Confirm playlists (including `stems_audio`) and year folders.

Do not overwrite ReCK / Mixed in Key key, BPM, comments, or cues in a later tag pass.

## Also from ATGR

- **ReCK** — writes Mixed in Key into Rekordbox.
- **RCT** — Rekordbox collection repair / relocate.

Buy and docs: [atgr.nl](https://atgr.nl/).
