# Security

ix is public. The Mac is not.

## Split
| Public (git) | Private (machine) |
|---|---|
| OSC address book | `~/.cursor/mcp.json` |
| Abstract tool schemas | `~/local_tools/mcp_adapters/` |
| Safety allowlists | Ollama binary + weights |
| Rehearsal UI | CDJ Ethernet / Pioneer sockets |
| Loopback runtime source | Absolute Unreal project paths |
| Loopback host:port names | LaunchAgents, `~/local_tools/ollama/env.sh` |

## Rules
1. **Loopback.** Every socket this project opens uses `127.0.0.1`. The safety module rejects `0.0.0.0`.
2. **Stdio MCP.** Prefer child-process MCP over HTTP. If HTTP is required, bind loopback.
3. **Circuit breaker.** DAW/DCC/UE tool calls go through `sanitize_tool_call`. Unknown commands die. Volume cannot exceed 0 dB.
4. **No secrets in git.** `.env`, MCP live config, adapter private scripts, and model files are gitignored. Example MCP uses `${HOME}` placeholders.
5. **Ollama off-repo.** Install with Homebrew (or the vendor installer) outside git. Models under `~/local_tools/ollama/models`. Set `OLLAMA_HOST=127.0.0.1:11434`. This repo only probes that URL.
6. **Do not read live MCP into commits.** Status checks may test `exists(~/.cursor/mcp.json)` but must not dump its contents.

## Ports and names in public docs

Publishing `127.0.0.1:9000`, `127.0.0.1:11434`, OSC paths like `/rekordbox/bpm`, and MCP *example* server names is **not** a remote hole.

Those numbers are not credentials. `127.0.0.1` is this machine talking to itself. A stranger on the internet cannot open your loopback. Malware that is already running as you can find the same listeners with `lsof` whether or not the README lists them.

Safe to commit:

- Loopback host:port pairs
- OSC address names and hall names
- Abstract schemas and `schemas/mcp.example.json` with `${HOME}` and `127.0.0.1`

Keep off git:

- Live `~/.cursor/mcp.json`
- Adapter code that talks to CDJ Ethernet, LAN IPs, or Pioneer sockets
- Absolute `/Users/<name>/` paths
- Tokens, `.env`, GGUF weights, `~/.ollama` identity keys
- Mail notify address (`~/local_tools/secrets/notify.enc`, AES via `box.py`)
- Any listen address that is not `127.0.0.1` (`0.0.0.0`, LAN IP, public DNS, ngrok, Tailscale serve)

The residual risk is **local**: a poisoned prompt or a malicious PR that already has MCP can use those names to press DAW/UE buttons. Allowlists exist for that. Hiding port numbers in markdown would not stop it.

## Threat notes
An LLM with MCP can stop playback mid-set or delete a scene object. Allowlists exist because prompt injection is a live-show risk, not a hypothetical.
