import { FORBIDDEN_BIND_HOSTS } from "./paths";

export const ALLOWED_DAW_COMMANDS = [
  "play",
  "stop",
  "set_tempo",
  "arm_track",
  "read_tempo",
] as const;

export const ALLOWED_DJ_COMMANDS = [
  "read_bpm",
  "read_fader",
  "read_beat_phase",
  "read_track_id",
] as const;

export const ALLOWED_UE_COMMANDS = [
  "set_cache_time",
  "set_density",
  "set_emissive",
  "inspect_level",
] as const;

export const MAX_VOLUME_DB = 0;

export type ToolFamily = "daw" | "dj" | "ue" | "dcc";

const ALLOWLIST: Record<ToolFamily, readonly string[]> = {
  daw: ALLOWED_DAW_COMMANDS,
  dj: ALLOWED_DJ_COMMANDS,
  ue: ALLOWED_UE_COMMANDS,
  dcc: ["inspect_scene", "export_fbx", "list_nodes"],
};

export class SafetyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SafetyError";
  }
}

export function assertLoopbackHost(host: string): string {
  const normalized = host.trim().toLowerCase();
  if ((FORBIDDEN_BIND_HOSTS as readonly string[]).includes(normalized)) {
    throw new SafetyError(
      `Refusing to bind ${host}. IX sockets listen on 127.0.0.1 only.`,
    );
  }
  if (normalized !== "127.0.0.1" && normalized !== "localhost") {
    throw new SafetyError(
      `Host '${host}' is not loopback. Bind 127.0.0.1.`,
    );
  }
  return "127.0.0.1";
}

export function sanitizeToolCall(
  family: ToolFamily,
  command: string,
  params: Record<string, number | string> = {},
): { command: string; params: Record<string, number | string> } {
  const allowed = ALLOWLIST[family];
  if (!allowed.includes(command)) {
    throw new SafetyError(
      `Action '${command}' blocked by the ${family} circuit breaker.`,
    );
  }

  const next = { ...params };
  if (typeof next.volume === "number" && next.volume > MAX_VOLUME_DB) {
    next.volume = MAX_VOLUME_DB;
  }
  return { command, params: next };
}
