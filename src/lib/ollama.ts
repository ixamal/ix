import { OLLAMA_LOOPBACK } from "./paths";

export type OllamaModel = {
  name: string;
  size: number;
  modifiedAt: string;
};

export type OllamaStatus = {
  online: boolean;
  endpoint: string;
  models: OllamaModel[];
  error: string | null;
};

const TIMEOUT_MS = 1800;

async function fetchOllama(path: string, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(`${OLLAMA_LOOPBACK}${path}`, {
      ...init,
      signal: controller.signal,
      cache: "no-store",
    });
  } finally {
    clearTimeout(timer);
  }
}

export async function probeOllama(): Promise<OllamaStatus> {
  try {
    const response = await fetchOllama("/api/tags");
    if (!response.ok) {
      return {
        online: false,
        endpoint: OLLAMA_LOOPBACK,
        models: [],
        error: `Ollama answered ${response.status}. Keep it bound to 127.0.0.1:11434.`,
      };
    }
    const payload = (await response.json()) as {
      models?: Array<{ name: string; size?: number; modified_at?: string }>;
    };
    return {
      online: true,
      endpoint: OLLAMA_LOOPBACK,
      models: (payload.models ?? []).map((model) => ({
        name: model.name,
        size: model.size ?? 0,
        modifiedAt: model.modified_at ?? "",
      })),
      error: null,
    };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Ollama is unreachable on loopback.";
    return {
      online: false,
      endpoint: OLLAMA_LOOPBACK,
      models: [],
      error: message.includes("abort")
        ? "No listener on 127.0.0.1:11434. Ollama stays off-repo by design."
        : message,
    };
  }
}

export async function chatOllama(input: {
  model: string;
  prompt: string;
}): Promise<{ reply: string; model: string }> {
  const status = await probeOllama();
  if (!status.online) {
    throw new Error(
      status.error ?? "Ollama is offline. Install it under ~/local_tools/ollama.",
    );
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60_000);
  try {
    const response = await fetch(`${OLLAMA_LOOPBACK}/api/generate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        model: input.model,
        prompt: input.prompt,
        stream: false,
      }),
      signal: controller.signal,
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`Ollama generate failed (${response.status}).`);
    }
    const payload = (await response.json()) as { response?: string };
    return {
      model: input.model,
      reply: payload.response?.trim() || "(empty reply)",
    };
  } finally {
    clearTimeout(timer);
  }
}
