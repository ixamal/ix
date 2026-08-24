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

## Rules
1. **Loopback.** Every socket this project opens uses `127.0.0.1`. The safety module rejects `0.0.0.0`.
2. **Stdio MCP.** Prefer child-process MCP over HTTP. If HTTP is required, bind loopback.
3. **Circuit breaker.** DAW/DCC/UE tool calls go through `sanitize_tool_call`. Unknown commands die. Volume cannot exceed 0 dB.
4. **No secrets in git.** `.env`, MCP live config, adapter private scripts, and model files are gitignored. Example MCP uses `${HOME}` placeholders.
5. **Ollama off-repo.** Install with the vendor installer into `~/local_tools/ollama`. Set `OLLAMA_HOST=127.0.0.1:11434`. This repo only probes that URL.
6. **Do not read live MCP into commits.** Status checks may test `exists(~/.cursor/mcp.json)` but must not dump its contents.

## Threat notes
An LLM with MCP can stop playback mid-set or delete a scene object. Allowlists exist because prompt injection is a live-show risk, not a hypothetical.
