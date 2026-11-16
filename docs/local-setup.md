# Local setup (Mac)

Clone next to the other ixamal repos:

```bash
mkdir -p ~/github/ixamal
git clone git@github.com:ixamal/ix.git ~/github/ixamal/ix
cd ~/github/ixamal/ix
npm install
./scripts/install-local-tools.sh
```

The installer creates off-repo directories only. It does **not** install Ollama:

- `~/local_tools/mcp_adapters`
- `~/local_tools/ollama`
- `~/.cursor/mcp.json` (from `schemas/mcp.example.json` if missing)

## Ollama (never inside this repo)

The control plane only probes `http://127.0.0.1:11434`. The binary, weights, LaunchAgent, and shell env stay off-repo.

On this Mac (2026-08-24): Homebrew formula `ollama` (CLI). Not the `ollama-app` cask. Not copied into git.

```bash
brew install ollama
mkdir -p ~/local_tools/ollama/models ~/local_tools/ollama/bin
ln -sfn "$(brew --prefix ollama)/bin/ollama" ~/local_tools/ollama/bin/ollama
```

Do **not** run `brew services start ollama`. That unit does not pin loopback or the models directory. Use a user LaunchAgent instead.

### Bind and model path

```bash
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS=~/local_tools/ollama/models
```

On this machine those exports live in `~/local_tools/ollama/env.sh` and are sourced from `~/.zshlocal/.zshrc` (both off-repo).

LaunchAgent label: `ai.ixamal.ollama` → `~/Library/LaunchAgents/ai.ixamal.ollama.plist` (off-repo). It must set:

| Key | Value |
| --- | --- |
| `OLLAMA_HOST` | `127.0.0.1:11434` |
| `OLLAMA_MODELS` | `$HOME/local_tools/ollama/models` (expand `$HOME` in the plist; do not commit the plist) |
| Program | `$(brew --prefix ollama)/bin/ollama serve` |

Confirm the listen address before pulling models:

```bash
lsof -nP -iTCP:11434 -sTCP:LISTEN
# NAME must be 127.0.0.1:11434 — never *:11434
```

Coder model (Cursor): `qwen2.5-coder:7b`. Crate music ID: `qwen2.5:7b` (pulled 2026-08-30). Both stay under `~/local_tools/ollama/models`.

```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
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

## MCP bridges (installed 2026-09-30)

Cursor launched from the Dock does not see `/opt/homebrew/bin` on its PATH. Use full command paths in `~/.cursor/mcp.json` (`/opt/homebrew/bin/uvx`, `/opt/homebrew/bin/node`) or the server fails at discovery. After editing, Cursor reloads the server on its own.

**Blender.** Any `bpy` script or `.blend` pipeline belongs in **[ixamal/stage](https://github.com/ixamal/stage)** (GPL). Do not add Blender files or MCP examples to ix. Configure `blender-dcc` only in your personal `~/.cursor/mcp.json` if you use it; adapter zip under `~/local_tools/mcp_adapters/blender/`.

**Rekordbox / Traktor (`dj-rekordbox`).** `~/local_tools/mcp_adapters/dj_bridge.js` is a dependency-free stdio MCP server run with Node. Read-only: `read_bpm`, `read_fader`, `read_beat_phase`, `read_track_id` (see `schemas/tools/rekordbox.json`), plus `dj_status`. It never sends OSC or binds a socket. It reads the latest value per OSC address from `ix_runtime` at `http://127.0.0.1:9100/status`, so start `npm run runtime` first. Something still has to send OSC to `127.0.0.1:9000`: Rekordbox does not emit it natively (Pro DJ Link / Traktor bridge not wired yet).

- `ix_runtime` and the UE OSC plugin both want UDP `127.0.0.1:9000`. Only one can own it at a time. Decide before the Floor Phase 3 UE work.

## ComfyUI (installed 2026-09-30, Floor Phase 1)

Lives off-repo in `~/local_tools/comfyui/`: `ComfyUI/` (git clone of Comfy-Org/ComfyUI), `.venv/` (uv, Python 3.13), `bin/` (shell shim), `workflows/`, `comfyui.log`. PyTorch MPS, `--force-fp16`, built-in Manager (`--enable-manager`), bound to `127.0.0.1:8188`.

### Models (off-repo weights, manifest in git)

Weights never enter git. The catalog is `schemas/comfyui-models.manifest.json`. Install or refresh with:

```bash
~/github/ixamal/ix/docs/examples/comfyui-models.sh
# long run (~40+ GB for all tiers):
COMFYUI_DETACH=1 ~/github/ixamal/ix/docs/examples/comfyui-models.sh
tail -f ~/local_tools/comfyui/reports/comfyui-models-*.log
```

| Tier | Purpose | Files (under `ComfyUI/models/`) |
| --- | --- | --- |
| `floor-sdxl` | Booth latency smoke, CRATER-adjacent stills | `checkpoints/sd_xl_turbo_1.0_fp16.safetensors` |
| `floor-flux` | Apache 2.0 stills (paid gigs) | `diffusion_models/flux1-schnell-fp8.safetensors`, `clip/clip_l.safetensors`, `clip/t5xxl_fp16.safetensors`, `vae/ae.safetensors` |
| `ui-zimage` | ComfyUI **Z-Image Turbo** template (browser **Run**) | `diffusion_models/z_image_turbo_bf16.safetensors`, `text_encoders/qwen_3_4b.safetensors`, shares `vae/ae.safetensors` with FLUX |

One tier only: `COMFYUI_TIERS=floor-sdxl docs/examples/comfyui-models.sh`. Dry run: `COMFYUI_DRY_RUN=1`.

**Licenses.** SDXL Turbo: Stability Community License (register before commercial use). FLUX.1 schnell: Apache-2.0. Z-Image: see upstream + Comfy-Org repack.

**Hugging Face gate.** FLUX encoder downloads need the [FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell) license accepted, then `huggingface-cli login` or `export HF_TOKEN=...`. Comfy-Org Z-Image and SDXL Turbo URLs are ungated in normal use.

**Verify SDXL Turbo (already on this Mac):**

```bash
shasum -a 256 ~/local_tools/comfyui/ComfyUI/models/checkpoints/sd_xl_turbo_1.0_fp16.safetensors
# expect e869ac7d6942cb327d68d5ed83a40447aadf20e0c3358d98b2cc9e270db0da26
```

Example workflows (copy to `~/local_tools/comfyui/workflows/` or run by path): `docs/examples/comfyui/floor_sdxl_turbo_test.json`, `docs/examples/comfyui/floor_simple_spotlight.json`. SDXL Turbo: 1 step, 512×512, `SDTurboScheduler`, cfg 1.0. First load ≈ 26 s, then ≈ 0.25 s/frame warm on M5 Max.

### Shell

`comfy` is not on the system PATH. The venv python must stay off PATH too, or it shadows whatever `python3` the shell already uses. Same pattern as Ollama: an off-repo env file, sourced from `~/.zshlocal/.zshrc` (which `~/.zshrc` already loads).

```bash
mkdir -p ~/local_tools/comfyui/bin
ln -sfn ~/local_tools/comfyui/.venv/bin/comfy ~/local_tools/comfyui/bin/comfy
```

`~/local_tools/comfyui/env.sh` prepends that `bin/` directory only. `~/.zshlocal/.zshrc` sources it. Both files stay off-repo. New interactive zsh sessions then resolve `comfy`. An already-open terminal needs `source ~/.zshlocal/.zshrc`, or a new tab.

```bash
comfy which
# workspace: ~/local_tools/comfyui/ComfyUI
```

### Server

LaunchAgent `ai.ixamal.comfyui` (on demand, not at login, so it does not hold memory beside the DAW). Start and stop with `launchctl`. `comfy launch` and `comfy stop` track a different pid and do not own this agent.

```bash
~/github/ixamal/ix/docs/examples/comfyui-start.sh     # start + open UI
launchctl kill TERM gui/$(id -u)/ai.ixamal.comfyui   # stop
comfy system-stats                                    # answers only while the agent is up
```

### Prompt

SDXL Turbo does not use the stock SD 1.5 graph. `comfy run --prompt "…"` builds that SD 1.5 graph and will not match this checkpoint. Edit the positive `CLIPTextEncode` text in a workflow JSON that already has `SDTurboScheduler`, 1 step, cfg 1.0, and 512×512, then run the file.

```bash
comfy run \
  --workflow ~/github/ixamal/ix/docs/examples/comfyui/floor_sdxl_turbo_test.json \
  --host 127.0.0.1 --port 8188 --wait
```

Novice one-liner (uses SDXL Turbo checkpoint, not the broken default UI graph):

```bash
comfy run --where local \
  --prompt "a red apple on a wooden table" \
  --set checkpoint=sd_xl_turbo_1.0_fp16.safetensors \
  --set steps=1 --set cfg=1 \
  --host 127.0.0.1 --port 8188 --wait
```

Without `--wait` the command queues and prints a `prompt_id`. `comfy jobs status <prompt_id>` reads it. Output PNGs land in `~/local_tools/comfyui/ComfyUI/output/`.

### MCP (`comfyui`)

Official [Comfy-Org/comfy-mcp](https://github.com/Comfy-Org/comfy-mcp) + `comfy-cli`, both in the ComfyUI venv. `~/.cursor/mcp.json` runs `${HOME}/local_tools/comfyui/.venv/bin/comfy-mcp` with `COMFY_BIN` and `COMFYUI_URL=http://127.0.0.1:8188`. `comfy-cli` tracking disabled; default workspace set.

- `run_workflow` with `wait=true` errors; submit with `wait=false`, then `job(action="status")`.
- Circuit-break: `partner_generate` / paid templates spend Comfy credits; `install_node`, `update_comfyui`, `switch_comfyui_version` change the install. Ask David first.

## Alkalurop org bridge (monthly 15th)

Public [ixamal](https://github.com/ixamal) originals are mirrored into the [alkalurop](https://github.com/alkalurop) org. The org section landing page is [`alkalurop/.github`](https://github.com/alkalurop/.github) (`profile/README.md`). Day-to-day work stays on ixamal.

**Tracker.** Issues, milestones, and labels live on **ixamal**. The bridge copies git (code + docs). It does not copy GitHub issue metadata. See `docs/tracker.md`. Skip the Agents tab.

```bash
# First / manual run (uses local `gh` as org admin; no tokens in git)
~/github/ixamal/ix/docs/examples/alkalurop-bridge.sh

# Load the 15th-of-month 15:00 job
cp ~/github/ixamal/ix/docs/examples/ai.ixamal.alkalurop-bridge.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.ixamal.alkalurop-bridge.plist
```

Log: `/tmp/ix-alkalurop-bridge.log`. `alkalurop/ix` cannot use GitHub’s transfer redirect from the old path — the script checks `owner.login` is `alkalurop` before it treats the dest as present.
