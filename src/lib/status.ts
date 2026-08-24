import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

import { probeOllama, type OllamaStatus } from "./ollama";
import {
  LOCAL_ADAPTERS_DIR,
  LOCAL_OLLAMA_DIR,
  LOCAL_TOOLS_ROOT,
  OSC_LOOPBACK_HOST,
  OSC_LOOPBACK_PORT,
  RUNTIME_HTTP_PORT,
} from "./paths";
import { getTelemetry, type TelemetrySnapshot } from "./osc-bus";

export type Probe = {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  location: "off-repo" | "loopback" | "workspace";
};

export type RigStatus = {
  generatedAt: number;
  home: string;
  clonePath: string;
  ollama: OllamaStatus;
  telemetry: TelemetrySnapshot;
  probes: Probe[];
};

function expandHome(path: string): string {
  if (path.startsWith("~/")) return join(homedir(), path.slice(2));
  return path;
}

async function probeRuntimeHttp(): Promise<Probe> {
  const url = `http://${OSC_LOOPBACK_HOST}:${RUNTIME_HTTP_PORT}/health`;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 800);
    const response = await fetch(url, { signal: controller.signal, cache: "no-store" });
    clearTimeout(timer);
    const body = (await response.json().catch(() => ({}))) as {
      host?: string;
      oscPort?: number;
    };
    const host = body.host ?? "";
    const ok = response.ok && host === "127.0.0.1";
    return {
      id: "osc-runtime",
      label: "OSC loopback runtime",
      ok,
      detail: ok
        ? `Listening on ${host}:${body.oscPort ?? OSC_LOOPBACK_PORT}`
        : `Runtime answered but refused non-loopback bind (${host || response.status}).`,
      location: "loopback",
    };
  } catch {
    return {
      id: "osc-runtime",
      label: "OSC loopback runtime",
      ok: false,
      detail: `No process on ${url}. Start with npm run runtime.`,
      location: "loopback",
    };
  }
}

export async function getRigStatus(): Promise<RigStatus> {
  const ollama = await probeOllama();
  const adapters = expandHome(LOCAL_ADAPTERS_DIR);
  const ollamaDir = expandHome(LOCAL_OLLAMA_DIR);
  const tools = expandHome(LOCAL_TOOLS_ROOT);
  const mcp = join(homedir(), ".cursor/mcp.json");

  const probes: Probe[] = [
    {
      id: "ollama",
      label: "Ollama oracle",
      ok: ollama.online,
      detail: ollama.online
        ? `${ollama.models.length} model${ollama.models.length === 1 ? "" : "s"} on ${ollama.endpoint}`
        : ollama.error ?? "Offline",
      location: "off-repo",
    },
    await probeRuntimeHttp(),
    {
      id: "local-tools",
      label: "Off-repo local_tools",
      ok: existsSync(tools),
      detail: existsSync(tools)
        ? `Present at ${LOCAL_TOOLS_ROOT}`
        : `Missing. Run scripts/install-local-tools.sh`,
      location: "off-repo",
    },
    {
      id: "adapters",
      label: "MCP adapters directory",
      ok: existsSync(adapters),
      detail: existsSync(adapters)
        ? `Present at ${LOCAL_ADAPTERS_DIR}`
        : "Adapters stay out of git on purpose.",
      location: "off-repo",
    },
    {
      id: "ollama-dir",
      label: "Ollama install prefix",
      ok: existsSync(ollamaDir),
      detail: existsSync(ollamaDir)
        ? `Prefix ready at ${LOCAL_OLLAMA_DIR}`
        : "Create with the local tools installer. Never vendor the binary here.",
      location: "off-repo",
    },
    {
      id: "mcp",
      label: "Global MCP config",
      ok: existsSync(mcp),
      detail: existsSync(mcp)
        ? "Found ~/.cursor/mcp.json (contents are never read into git)."
        : "Create ~/.cursor/mcp.json from schemas/mcp.example.json",
      location: "off-repo",
    },
  ];

  return {
    generatedAt: Date.now(),
    home: homedir(),
    clonePath: join(homedir(), "github/ixamal/ix"),
    ollama,
    telemetry: getTelemetry(),
    probes,
  };
}
