# IX context (synced for desktop + mobile agents)

Cursor desktop chats do not sync to the iPhone app. Cloud Agent threads do. Long-term decisions live in this repo so any device can read them.

Source: Gemini architecture conversation, 2026-08-24, brought into ix by the first Valhalla cloud agent.

## Decision
ix is Valhalla: Cursor is the control plane. Ollama, MCP hardware bridges, and live sockets stay **off-repo**.

## Stack
1. Unreal Engine 5.x on Apple Silicon / macOS (Blueprints + C++ now; Verse later).
2. Niagara 3D grid fluids + 15s Niagara Sim Cache. No Houdini required for v1.
3. Rekordbox / Traktor / Pro DJ Link → OSC on `127.0.0.1:9000`.
4. Optional later: Houdini HDA / OpenVDB / NanoVDB (ASWF, Metal-capable).
5. Global MCP: `~/.cursor/mcp.json`. Adapters: `~/local_tools/mcp_adapters/`.
6. Ollama (installed on the Mac 2026-08-24): Homebrew CLI, LaunchAgent `ai.ixamal.ollama`, `OLLAMA_HOST=127.0.0.1:11434`, models in `~/local_tools/ollama/models`. Coder: `qwen2.5-coder:7b`. Crate music ID: `qwen2.5:7b`. Not in git. See `docs/local-setup.md`.

## Crate + hardware
Unknown Album dump **executed**. Inbox catalog + Ollama (`qwen2.5:7b`) **executed**. Traktor NML remapped. DJCU2 **worked**. Path-stable (TODO 3). Accapella + `EDM, …` **closed** (TODO 4 / 4a). `House, …` + Hip Hop spelling **closed** (TODO 8 / 9). Music.app same-file rows **closed** (TODO 16). Locate/! rows **relinked** (TODO 18). Items **5 / 5b / 6 omitted**. Floor **10** parked. Stems: Acapella do not stem; Afro House done. **Next: Alternative tracks 1–3.** NI/Maschine is **11+**, parked in [ixamal/blackhole](https://github.com/ixamal/blackhole). Bridge: [ATGR DJCU2](https://atgr.nl/). Step log: `docs/onetagger.md`. Links: `docs/notes.md`.

## Immediate UE work (on the Mac, not in this cloud VM)
1. Enable OSC plugin, listen `127.0.0.1:9000`.
2. Build a Grid 3D Gas/Smoke Niagara system. Record 15s sim cache.
3. Bind `/rekordbox/bpm` and `/rekordbox/fader` to cache Explicit Time / density.

## Sync back to Mac
- Cloud Agent chat is visible at cursor.com/agents and in the Mac Agents panel.
- File changes land on Mac after pull into `~/github/ixamal/ix`.
- Do not rely on desktop Composer history. Rely on these markdown files.

## Deeplink to continue on desktop
https://cursor.com/link/prompt?text=Read%20.cursor/context.md%20and%20docs/architecture.md.%20Continue%20the%20IX%20Valhalla%20rig%3A%20wire%20UE5%20OSC%20on%20127.0.0.1%3A9000%20to%20a%2015s%20Niagara%20sim%20cache.
