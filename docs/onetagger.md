# OneTagger

[OneTagger](https://onetagger.github.io/) is a **desktop + CLI tagger** (Rust), not a Python module and not an LLM. It looks up **Beatport, Traxsource, Discogs** (and others) and writes tags on the files you point it at. TODO **5 / 5b / 6** are omitted — Ollama is not a substitute store pass.

Install lives off-repo: `~/local_tools/onetagger/` (app, CLI 1.7.0, sample, work). Not in git.

## Goal on this Mac

Replace Apple Music’s **genre** (and Beatport **style**/subgenre) with store-database values. Do **not** use the current Music.app genre as source. Do **not** overwrite ReCK / Mixed in Key **key, BPM, comments, or cues**.

**Energy:** OneTagger does not pull Mixed in Key energy. Auto energy is Spotify Audio Features (later, needs Spotify login). Keep MiK/ReCK energy as-is for now.

## Two layers (2026-08-30)

Music.app does **not** re-read file tags. Genre in Songs / the column browser comes from the library database. Cloud-download icons are library rows; some never had a local file. **Sync Library is Off** on this Mac — keep it off (DJ crate stays local). Same two-layer write applies to leftover TODO **8** (`House, …`) and **9** (Hip Hop / Hip-Hop).

1. **Files** — in-place on owned `Media.localized` (`.mp3` / `.m4a` only, never `.m4p`). Music.app quit. Hardlinks under `~/local_tools/onetagger/work/`.
2. **Library** — AppleScript `set genre` on Music.app tracks. File writes alone left the UI looking unchanged. Generic specimen (no live paths, do not run): `docs/examples/music-set-genre.applescript`.

## Steps we ran

1. Confirmed OneTagger is Rust CLI (`~/local_tools/onetagger/cli/onetagger-cli`), not a Python module or LLM.
2. Sample: four owned copies in `sample/`. Config `genre-only.json` (genre + style only; `overwrite: false`; `overwriteTags: ["genre","style"]`). Beatport returned non-JSON (API v4; 1.7.0 is the latest Mac release). Discogs wrote `Electronic` on Roads / Gravity. BPM unchanged.
3. **Accapella files.** 9 owned hardlinks in `work/acapella/`. CLI: Beatport/Traxsource failed; Discogs Ok on 7, miss on `Story Of A DJ` and `It's All Right`. Discogs wrote parent-release `Electronic`. All 9 set to **Acapella** (genre only).
4. **EDM probe (do not skip).** Beatport + Traxsource on four `EDM, House` / `EDM, Techno` files: no usable writes. Discogs then wrote `Electronic` and tagged DJ Ino `Revolution` as **Hip Hop** (compilation collision). Those four genres restored. Discogs not used for the batch.
5. **File promote.** `~/local_tools/onetagger/strip_edm_prefix.py` stripped `EDM, ` on **11,031** owned files (`House`, `Techno`, `House, Deep`, …). Accapella spellings → `Acapella`. Log: `work/edm-strip.log`. Disk leftover `EDM*`: **0**. BPM unchanged on spot checks.
6. **Music.app still showed `EDM, Accapella`.** Column browser is the library DB, not the files. 11,731 `EDM*` library rows vs 11,031 files (cloud-only extras).
7. **Library promote.** AppleScript one-track `set genre` (bulk list-set fails). 12 `EDM, Accapella` → `Acapella`; **11,719** other `EDM, …` promoted. Music.app leftover `EDM*`: **0**. **14** tracks `Acapella`. Click off a stale genre selection to refresh the column browser.

**Recurrence (2026-09-04).** Consolidation copied tracks that had never been through this pass, so `EDM, House` / `EDM, Ambient` / `EDM, Electronica` came back (229 rows). The Terrarum recover the same afternoon brought **66** more — same prefix still on those files. Do not re-run the OneTagger strip script. The crate command is `PYTHONPATH=crate python3 -m ix_crate music-genre --execute` (file tags + library, `--passes` for reorder). Never mutagen-write `.wav`. Leftover `EDM*`: **0** again. Click off a stale genre in the column browser. Detail: `docs/crate.md`.

Never move files. Never run this on Apple Music streams.

## Specimen (not the live driver)

The script that ran lives under `~/local_tools/onetagger/`, not in git. `docs/examples/music-set-genre.applescript` is a path-free reconstruction of that pass so others can review **4a**: library `set genre`, one track at a time, skip `.m4p`. It is not a tool. Do not execute it against a live crate.

## Beatport (TODO 5 omitted)

OneTagger **1.7.0 will not grow Beatport**. Last [Mac release](https://github.com/Marekkon5/onetagger/releases/tag/1.7.0) is 2023-08-03. Beatport is [API v4](https://api.beatport.com/v4/docs/) now ([#486](https://github.com/Marekkon5/onetagger/issues/486), [#518](https://github.com/Marekkon5/onetagger/issues/518)). Community [PR #526](https://github.com/Marekkon5/onetagger/pull/526) speaks v4 on Linux; unmerged since 2026-05; no official Mac build. [PR #523](https://github.com/Marekkon5/onetagger/pull/523) was an earlier scrape fix. Do not compile those unless David asks. Catalog as of the genre pass stands.

```bash
~/local_tools/onetagger/cli/onetagger-cli autotagger \
  --config ~/local_tools/onetagger/genre-only.json \
  --path ~/local_tools/onetagger/sample
```

Do not re-run Discogs on the old `EDM, …` set.
