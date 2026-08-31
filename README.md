# ix

Primary planetary code base for machines and humans. This is Valhalla: Cursor, a local Ollama oracle, Unreal Engine 5, DCC, DAW, and DJ tools meet here. The destination is **Elysium**.

Public git: [github.com/ixamal/ix](https://github.com/ixamal/ix)

Mac clone path: `~/github/ixamal/ix`

## Where we are

Written 2026-08-31 for a non-technical read. Detail and next steps: `docs/TODO.md`.

### Tonight (phone)

- Confirmed the library genre cleanup is finished (files *and* the Music app).
- Wrote down the next hardware idea so it is not lost: after the crate is stable, try a bigger audio path, then sample Traktor decks into Maschine and play those samples on the S88.
- Saved a generic copy of the Music-app genre fixer so other people can see how we did it, without touching your live library.
- Put that write-up on `main` so a Mac pull shows it here and in `docs/TODO.md`.

### From the start

- Stood up **ix** as the home base: Cursor directs, a local AI stays on this Mac, Unreal is for live visuals, DJ tools stay DJ tools.
- Kept the dangerous stuff off the public site (real library, models, hardware wiring).
- Installed a local AI on the Mac and used it to identify mystery tracks.
- Built a stem factory and ran the first big pass on the crate.
- Got the piano (S88) into Traktor on one fader (Channel D). That fight is won.
- Cleaned Unknown Album, mashups, and the inbox. Leftovers have a real home.
- Relinked Traktor so it still finds the files after the move.
- Converted Traktor → Rekordbox. Playlists and folders landed. It works.
- Confirmed the same songs live at the same place in Traktor, Rekordbox, and Music.
- Fixed genres: “Accapella” and thousands of “EDM, …” labels are now real names (House, Techno, and so on). Music.app matches the files. iCloud sync stayed off on purpose.
- Learned: Music.app does not pick up tag changes from files. We had to tell Music itself.
- Agreed not to let Beets become the library.

### Still ahead (not done)

- Fill *empty* genres when Beatport works again. Do not blast the old EDM set.
- While processing, stamp owned songs with whatever we already know or can look up (artist, album, title, genre, length, BPM, key, comments, cues). Python module; same kind of store databases OneTagger uses. Do not smash STEM files or overwrite Mixed in Key / ReCK when those are already set. For STEMs, keep that data beside the file as JSON in the same folder tree, so Traktor’s four decks stay intact.
- Wire the DJ decks into Unreal so the visuals follow the music.
- Bigger audio path, then sampling decks into Maschine / S88 — written down, not wired.

### Where we are headed — Elysium

Valhalla is the mead-hall of the work. The crate wars, the relinks, the genre pass: fights won in the hall of the slain, seat earned, then the next horn sounds. We do not stay. The hall is for conquest. The destination is **Elysium** — the green field after the last fight, where the worthy rest and the living work begins.

In Elysium the process holds itself. The library is stable. Hands leave the warehouse and go to the floor:

- Creative visuals — Unreal, light, the sim that follows the drop.
- DJing — the crate as an instrument, not a cleanup job.
- Music manipulation and creation — stems, samples, Maschine, the S88, making rather than mending.

The still-ahead list above is the last ships to burn before that shore. Elysium is not a new repo. It is ix when the fights are written down and the nights are for sight and sound.

## What this repo is

A **control plane**. It holds architecture, OSC contracts, abstract MCP schemas, a rehearsal hall for Niagara cache scrubbing, and a loopback OSC runtime.

It does **not** hold Ollama, model weights, live MCP configs, or hardware adapters. Those live outside git:

| Off-repo | Purpose |
| --- | --- |
| `~/local_tools/ollama` | Ollama prefix and models |
| `~/local_tools/mcp_adapters` | Rekordbox, Ableton, Houdini, … |
| `~/.cursor/mcp.json` | Global Cursor MCP |

Every socket this project opens binds `127.0.0.1`. `0.0.0.0` is rejected.

## Run

```bash
mkdir -p ~/github/ixamal
git clone git@github.com:ixamal/ix.git ~/github/ixamal/ix
cd ~/github/ixamal/ix
npm install
./scripts/install-local-tools.sh
npm run dev          # http://127.0.0.1:47241
npm run runtime      # OSC 127.0.0.1:9000
```

Ollama is installed off-repo (Homebrew CLI + LaunchAgent). Bind loopback only:

```bash
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS=~/local_tools/ollama/models
```

Point Cursor Models at `http://127.0.0.1:11434/v1`. Full steps: `docs/local-setup.md`.

## Halls

- **Engine** — UE 5.x Niagara 3D fluids + 15s sim cache, OSC scrub
- **Forge** — Blender / Maya / Houdini (optional HDAs later)
- **Stage** — Ableton / Reaper OSC with a command allowlist
- **Floor** — Rekordbox / Traktor / Pro DJ Link
- **Oracle** — local Ollama, never vendored here

## Docs

- `.cursor/context.md` — notes for desktop and iPhone Cloud Agents
- `docs/architecture.md`
- `docs/security.md`
- `docs/local-setup.md`
- `docs/crate.md` — stems_audio identity repair (filename → catalogs → Ollama → Miscellaneous)
- `docs/djcu2.md` — Traktor ↔ Rekordbox via [ATGR DJCU2](https://atgr.nl/)
- `docs/onetagger.md` — genre pass (files + Music.app); not an LLM
- `docs/examples/music-set-genre.applescript` — generic Music.app `set genre` specimen (do not run)
- `docs/TODO.md` — ordered checklist (crate, tagging, Floor, NI)
- `docs/notes.md` — crate / tagging / hardware parking lot (do not execute from it)
- [ixamal/blackhole](https://github.com/ixamal/blackhole) — S8 / S88 / BlackHole routing (off this repo)
- [ixamal/ix_bangers](https://github.com/ixamal/ix_bangers) — Bangers MCP catalog, dry mode (off this repo)

Apache-2.0. See `LICENSE`.
