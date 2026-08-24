# Local setup (Mac)

Clone next to the other ixamal repos:

```bash
mkdir -p ~/github/ixamal
git clone git@github.com:ixamal/ix.git ~/github/ixamal/ix
cd ~/github/ixamal/ix
npm install
./scripts/install-local-tools.sh
```

The installer creates off-repo directories only:

- `~/local_tools/mcp_adapters`
- `~/local_tools/ollama`
- `~/.cursor/mcp.json` (from `schemas/mcp.example.json` if missing)

## Ollama (never inside this repo)

```bash
# vendor installer, then:
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS=~/local_tools/ollama/models
ollama serve
ollama pull qwen2.5-coder:7b   # pick a model that fits the machine
```

In Cursor: Settings → Models → OpenAI-compatible endpoint `http://127.0.0.1:11434/v1`.

## Run the control plane

```bash
npm run dev          # http://127.0.0.1:47241
npm run runtime      # OSC 127.0.0.1:9000 + health :9100
```

## Unreal Engine 5 (on the Mac)

1. Enable the OSC plugin. Listen `127.0.0.1:9000`.
2. Author a Niagara Grid 3D Gas/Smoke emitter.
3. Record a 15-second Niagara Sim Cache.
4. Expose Age / Explicit Time and density on a Blueprint; map `/rekordbox/bpm`, `/rekordbox/fader`, `/rekordbox/beat_phase`.

Global MCP lives in `~/.cursor/mcp.json`, not in this workspace.
