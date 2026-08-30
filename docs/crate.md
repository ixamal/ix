# Crate identity repair

`stems` writes STEM siblings. [music_migration](https://github.com/ixamal/music_migration) remaps Traktor/Rekordbox after files move. **This package** repairs identity in `~/Music/stems_audio`.

Audio never enters git. Reports and lookup cache: `~/local_tools/crate/`.

## Cascade (every family)

1. **Filename** — `Artist - Title` or `Artist - Album - Title`, junk stripped. `Artist _ Title` and `Artist | Title` only when the left side is ≤4 words.
2. **Tags** — mix-file tags only; ignore role-file `instrumental` / `vocals`.
3. **iTunes + Deezer** — title + duration (or both catalogs agree). Mashups, clips, and mixes ≥20 min stay out.
4. **MusicBrainz** — fill album only when artist is already known.
5. **Ollama** — `127.0.0.1:11434` JSON. Default `qwen2.5:7b`. Coder models are skipped. Artist must appear in the filename.
6. **`Compilations/Mashups/Miscellaneous/`** — leftover bucket after lookup. Never `Unknown Artist` / `Unknown Album`. Scan still starts from `_outliers/Inbox/`.

No skips. Families (mix + stem + vocals/instrumental) always move together.

Mashups: `Compilations/Mashups/{Artist}/`. Also moves `{Artist}/Mashups/` and placeholder albums (`Unknown Album`, `_ album title goes here _`). Artist description is the parent folder name.

## Commands

```bash
cd ~/github/ixamal/ix
cd crate && PYTHONPATH=. python3 -m unittest tests.test_identify -q
cd ~/github/ixamal/ix
PYTHONPATH=crate python3 -m ix_crate unknown-album            # dry-run + lookups
PYTHONPATH=crate python3 -m ix_crate unknown-album --offline  # filename/tags only
PYTHONPATH=crate python3 -m ix_crate unknown-album --execute  # after you read the report
PYTHONPATH=crate python3 -m ix_crate outliers                 # re-ID _outliers/Inbox (dry-run)
PYTHONPATH=crate python3 -m ix_crate outliers --execute       # after you read the outliers report
PYTHONPATH=crate python3 -m ix_crate mashups                  # Compilations/Mashups dry-run
PYTHONPATH=crate python3 -m ix_crate mashups --execute
```

## After this dump

Unknown Album, mashups, and Inbox are executed. `_outliers` is gone. Unidentified leftovers: `Compilations/Mashups/Miscellaneous/`.

1. Traktor remapped. DJCU2 Traktor → Rekordbox confirmed (`docs/djcu2.md`, [atgr.nl](https://atgr.nl/)).
2. Confirm path-stable crate across Music.app / Rekordbox / Traktor.

Never write Apple Music `Media.localized`. Never commit `/Users/<name>/` paths.
