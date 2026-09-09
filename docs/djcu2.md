# DJCU2 — Traktor ↔ Rekordbox

[ATGR](https://atgr.nl/) (Mixmaster G) makes **DJ Conversion Utility Two**. Site: [atgr.nl](https://atgr.nl/). It is the crate bridge on this Mac after identity repair. ix does not replace it.

DJCU2 moves playlists, cues, loops, and beatgrids between Traktor, Rekordbox, Serato, Engine, VirtualDJ, and djay. Confirmed on this machine 2026-08-30: full Traktor → Rekordbox after the `stems_audio` dump. It works. We do not reimplement that convert.

Playlist **membership** between Music.app, Traktor NML, and `rekordbox.xml` is crate `crates` (`docs/crate.md`). That pass never writes POSITION_MARK / CUE_V2 / TEMPO / comments. Use DJCU2 when a track is missing from Rekordbox and you need its cues and grids copied in.

## Process

STEMIT crates, titles, and `STEMIT/Genres` live in Traktor NML (source of truth). Crate promotes STEMIT + nested Genres into `rekordbox.xml`. DJCU2 is optional for cues/grids on tracks Rekordbox does not already have — it is **not** the playlist-folder bridge.

1. Keep Traktor as it is. Confirm STEMIT + Genres there.
2. Quit Rekordbox (Traktor can stay open unless you pass `--nml`).
3. `PYTHONPATH=crate python3 -m ix_crate stemit --genres --execute`
4. Reopen Rekordbox. In the **rekordbox xml** tree, expand STEMIT → Genres. Drag that folder into the collection if the XML crate is only a browser (Preferences → rekordbox xml). Delete an old flat STEMIT folder in the collection first if it would duplicate.
5. Snapshot DBs into `databases/` on this Mac (gitignored). See `databases/README.md`.

2026-09-08: Music.app playlists landed in `rekordbox.xml/MUSIC/` via `crates` (not DJCU2). David imported that folder into collection and is playing. STEMIT still `stemit --genres`. DJCU2 stays the cue/grid convert.

Do not overwrite ReCK / Mixed in Key key, BPM, comments, or cues in a later tag pass. Do not Discogs-blast.

## Also from ATGR

- **ReCK** — writes Mixed in Key into Rekordbox.
- **RCT** — Rekordbox collection repair / relocate.

Buy and docs: [atgr.nl](https://atgr.nl/).
