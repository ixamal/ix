/**
 * Public path constants only. Never encode real machine tokens, absolute
 * user home expansions of secrets, or live MCP command lines here.
 *
 * Hardware adapters and Ollama live *outside* this git workspace.
 */

export const PUBLIC_CLONE_PATH = "~/github/ixamal/ix";
export const LOCAL_TOOLS_ROOT = "~/local_tools";
export const LOCAL_ADAPTERS_DIR = "~/local_tools/mcp_adapters";
export const LOCAL_OLLAMA_DIR = "~/local_tools/ollama";
export const GLOBAL_MCP_CONFIG = "~/.cursor/mcp.json";
export const OLLAMA_LOOPBACK = "http://127.0.0.1:11434";
export const OSC_LOOPBACK_HOST = "127.0.0.1";
export const OSC_LOOPBACK_PORT = 9000;
export const RUNTIME_HTTP_PORT = 9100;

export const FORBIDDEN_BIND_HOSTS = ["0.0.0.0", "::", "[::]"] as const;
