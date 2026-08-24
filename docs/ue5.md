# Unreal Engine 5 — first live slice

Do this on the Mac. This cloud workspace cannot run UE.

1. Enable **OSC** plugin. Listen `127.0.0.1:9000`. Never `0.0.0.0`.
2. Create a Niagara **Grid 3D Gas / Smoke** emitter.
3. Record a **15-second Niagara Sim Cache**.
4. On the cache component, expose **Age / Explicit Time** and a density scalar.
5. Blueprint map:
   - `/rekordbox/beat_phase` (0–1) → Explicit Time = phase × 15
   - `/rekordbox/bpm` → play rate
   - `/rekordbox/fader` → density / opacity
6. Optional: Unreal MCP via global `~/.cursor/mcp.json` (see `schemas/mcp.example.json`).

Houdini HDAs and NanoVDB are later. Niagara cache is the v1 path on Apple Silicon.
