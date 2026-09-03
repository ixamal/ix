# ix crate

Identify and rehome untagged files under `~/Music/stems_audio`. Dry-run by default.

See `docs/crate.md`.

```bash
PYTHONPATH=crate python3 -m ix_crate unknown-album
PYTHONPATH=crate python3 -m ix_crate outliers
PYTHONPATH=crate python3 -m ix_crate mashups
PYTHONPATH=crate python3 -m ix_crate music-dupes
PYTHONPATH=crate python3 -m ix_crate music-dupes --execute
PYTHONPATH=crate python3 -m ix_crate music-repair
PYTHONPATH=crate python3 -m ix_crate music-repair --execute
PYTHONPATH=crate python3 -m ix_crate music-fix --playlist Fix
PYTHONPATH=crate python3 -m ix_crate music-fix --playlist Fix --execute
PYTHONPATH=crate python3 -m ix_crate music-fix --library-va
PYTHONPATH=crate python3 -m ix_crate music-fix --library-va --execute
```

Leftovers after lookup go to `Compilations/Mashups/Miscellaneous/`. Dry-run is the default; pass `--execute` to move.

`music-dupes` finds Music.app Songs rows that share one file on disk (Show in Finder opens the same path). Dry-run is the default. `--execute` deletes the extra *library rows* only — the audio stays. Uses the stems factory Aqua HUD (`py.utils.progress`). `--no-gui` stays in the terminal.

`music-repair` relinks Songs rows with no file (Locate / !) to a unique match on disk, then fills empty artist/album/title (crate cascade) and empty genre (iTunes only). It does not move Media.localized.

`music-fix` fills artist / album / title / genre on a Music.app playlist (default `Fix`). Default is aggressive: AcoustID fingerprints, Shazam, duration-matched iTunes/Deezer. Unidentified leftovers are skipped (not labeled Various Artists). `--library-va` targets library rows whose artist is Various Artists. `--strict` is the old dual-catalog path. Never moves Media.localized. Screenshot-driven one-album Discogs (not a crate command): `docs/crate.md`.
