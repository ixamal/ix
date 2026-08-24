import { OSC_LOOPBACK_HOST, OSC_LOOPBACK_PORT } from "./paths";

export const OSC_ADDRESSES = {
  bpm: "/rekordbox/bpm",
  fader: "/rekordbox/fader",
  beatPhase: "/rekordbox/beat_phase",
  deck: "/rekordbox/deck",
  trackId: "/rekordbox/track_id",
  cacheTime: "/ue/niagara/cache_time",
  density: "/ue/niagara/density",
} as const;

export type OscSource = "rehearsal" | "loopback" | "hardware";

export type OscMessage = {
  address: string;
  args: Array<number | string>;
  receivedAt: number;
  source: OscSource;
};

export type TelemetrySnapshot = {
  bpm: number;
  fader: number;
  beatPhase: number;
  deck: number;
  trackId: string;
  cacheTime: number;
  density: number;
  updatedAt: number;
  source: OscSource;
  history: OscMessage[];
};

const CACHE_SECONDS = 15;
const HISTORY_LIMIT = 48;

const defaultSnapshot = (): TelemetrySnapshot => ({
  bpm: 126,
  fader: 0.62,
  beatPhase: 0,
  deck: 1,
  trackId: "rehearsal-grid",
  cacheTime: 0,
  density: 0.62,
  updatedAt: Date.now(),
  source: "rehearsal",
  history: [],
});

declare global {
  var __ixOscBus: TelemetrySnapshot | undefined;
}

function bus(): TelemetrySnapshot {
  if (!globalThis.__ixOscBus) {
    globalThis.__ixOscBus = defaultSnapshot();
  }
  return globalThis.__ixOscBus;
}

function asNumber(value: number | string | undefined, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

export function getTelemetry(): TelemetrySnapshot {
  return { ...bus(), history: [...bus().history] };
}

export function applyOscMessage(message: OscMessage): TelemetrySnapshot {
  const state = bus();
  const arg = message.args[0];

  switch (message.address) {
    case OSC_ADDRESSES.bpm:
      state.bpm = Math.min(220, Math.max(60, asNumber(arg, state.bpm)));
      break;
    case OSC_ADDRESSES.fader:
      state.fader = Math.min(1, Math.max(0, asNumber(arg, state.fader)));
      state.density = state.fader;
      break;
    case OSC_ADDRESSES.beatPhase:
      state.beatPhase = ((asNumber(arg, state.beatPhase) % 1) + 1) % 1;
      break;
    case OSC_ADDRESSES.deck:
      state.deck = Math.round(asNumber(arg, state.deck));
      break;
    case OSC_ADDRESSES.trackId:
      state.trackId = String(arg ?? state.trackId);
      break;
    case OSC_ADDRESSES.cacheTime:
      state.cacheTime = Math.min(
        CACHE_SECONDS,
        Math.max(0, asNumber(arg, state.cacheTime)),
      );
      break;
    case OSC_ADDRESSES.density:
      state.density = Math.min(1, Math.max(0, asNumber(arg, state.density)));
      break;
    default:
      break;
  }

  if (message.address !== OSC_ADDRESSES.cacheTime) {
    state.cacheTime = state.beatPhase * CACHE_SECONDS;
  }

  state.updatedAt = message.receivedAt;
  state.source = message.source;
  state.history = [{ ...message }, ...state.history].slice(0, HISTORY_LIMIT);
  return getTelemetry();
}

export function injectRehearsal(partial: {
  bpm?: number;
  fader?: number;
  beatPhase?: number;
}): TelemetrySnapshot {
  const now = Date.now();
  if (partial.bpm != null) {
    applyOscMessage({
      address: OSC_ADDRESSES.bpm,
      args: [partial.bpm],
      receivedAt: now,
      source: "rehearsal",
    });
  }
  if (partial.fader != null) {
    applyOscMessage({
      address: OSC_ADDRESSES.fader,
      args: [partial.fader],
      receivedAt: now,
      source: "rehearsal",
    });
  }
  if (partial.beatPhase != null) {
    applyOscMessage({
      address: OSC_ADDRESSES.beatPhase,
      args: [partial.beatPhase],
      receivedAt: now,
      source: "rehearsal",
    });
  }
  return getTelemetry();
}

export const oscListenTarget = `${OSC_LOOPBACK_HOST}:${OSC_LOOPBACK_PORT}`;
export const niagaraCacheSeconds = CACHE_SECONDS;
