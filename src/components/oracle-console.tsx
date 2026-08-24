"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { OllamaStatus } from "@/lib/ollama";
import { LOCAL_OLLAMA_DIR, OLLAMA_LOOPBACK } from "@/lib/paths";

export function OracleConsole() {
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [model, setModel] = useState("");
  const [prompt, setPrompt] = useState(
    "Map /rekordbox/beat_phase onto a 15 second Niagara sim cache.",
  );
  const [reply, setReply] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const pull = async () => {
      const response = await fetch("/api/ollama", { cache: "no-store" });
      const data = (await response.json()) as OllamaStatus;
      if (cancelled) return;
      setStatus(data);
      if (!model && data.models[0]) setModel(data.models[0].name);
    };
    void pull();
    const id = setInterval(() => void pull(), 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [model]);

  const ask = async () => {
    setBusy(true);
    setError(null);
    setReply(null);
    try {
      const response = await fetch("/api/ollama/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ model, prompt }),
      });
      const data = (await response.json()) as { reply?: string; error?: string };
      if (!response.ok) {
        setError(data.error ?? "Oracle refused the call.");
        return;
      }
      setReply(data.reply ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Oracle call failed.");
    } finally {
      setBusy(false);
    }
  };

  const online = status?.online ?? false;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-3">
            Loopback oracle
            <Badge variant={online ? "default" : "outline"}>
              {online ? "online" : "offline"}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm leading-6 text-muted-foreground">
          <p>
            Ollama is not in this git tree. The binary and weights belong under{" "}
            <code className="text-foreground">{LOCAL_OLLAMA_DIR}</code>. This hall only
            talks to <code className="text-foreground">{OLLAMA_LOOPBACK}</code>.
          </p>
          <p>
            Cursor Models → OpenAI-compatible base URL{" "}
            <code className="text-foreground">http://127.0.0.1:11434/v1</code>
          </p>
          {!online ? (
            <p className="text-foreground" role="status">
              {status?.error ??
                "No listener on 11434. That is expected until you install Ollama off-repo."}
            </p>
          ) : (
            <ul className="font-mono text-xs text-foreground">
              {status?.models.length ? (
                status.models.map((item) => (
                  <li key={item.name}>{item.name}</li>
                ))
              ) : (
                <li>Oracle is up, but no models are pulled yet.</li>
              )}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ask the local model</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Input
            value={model}
            onChange={(event) => setModel(event.target.value)}
            placeholder="model name (offline until Ollama is installed)"
            aria-label="Ollama model"
          />
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={5}
            className="min-h-28 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
            aria-label="Prompt"
          />
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => void ask()} disabled={busy || !online || !model}>
              {busy ? "Waiting on loopback…" : "Generate"}
            </Button>
            {!online ? (
              <p className="self-center text-xs text-muted-foreground">
                Generate stays disabled while 11434 is dark. That keeps weights off this
                repo.
              </p>
            ) : null}
          </div>
          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}
          {reply ? (
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-muted/40 p-4 font-mono text-xs leading-6">
              {reply}
            </pre>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
