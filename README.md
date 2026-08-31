# ix

Primary planetary code base for machines and humans. This is Valhalla: Cursor, a local Ollama oracle, Unreal Engine 5, DCC, DAW, and DJ tools meet here.

Public git: [github.com/ixamal/ix](https://github.com/ixamal/ix)

Mac clone path: `~/github/ixamal/ix`

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
