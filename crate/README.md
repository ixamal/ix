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
```

Leftovers after lookup go to `Compilations/Mashups/Miscellaneous/`. Dry-run is the default; pass `--execute` to move.

`music-dupes` finds Music.app Songs rows that share one file on disk (Show in Finder opens the same path). Dry-run is the default. `--execute` deletes the extra *library rows* only — the audio stays. Uses the stems factory Aqua HUD (`py.utils.progress`). `--no-gui` stays in the terminal.

`music-repair` relinks Songs rows with no file (Locate / !) to a unique match on disk, then fills empty artist/album/title (crate cascade) and empty genre (iTunes only). It does not move Media.localized.
