# ix crate

Identify and rehome untagged files under `~/Music/stems_audio`. Dry-run by default.

See `docs/crate.md`.

```bash
PYTHONPATH=crate python3 -m ix_crate unknown-album
PYTHONPATH=crate python3 -m ix_crate outliers
PYTHONPATH=crate python3 -m ix_crate mashups
```

Leftovers after lookup go to `Compilations/Mashups/Miscellaneous/`. Dry-run is the default; pass `--execute` to move.
