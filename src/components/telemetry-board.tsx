"use client";

import { useEffect, useRef, useState } from "react";

import { NiagaraChamber } from "@/components/niagara-chamber";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import type { TelemetrySnapshot } from "@/lib/osc-bus";
import { niagaraCacheSeconds } from "@/lib/osc-bus";

const empty: TelemetrySnapshot = {
  bpm: 126,
  fader: 0.62,
  beatPhase: 0,
  deck: 1,
  trackId: "rehearsal-grid",
  cacheTime: 0,
  density: 0.62,
  updatedAt: 0,
  source: "rehearsal",
  history: [],
};

export function TelemetryBoard() {
  const [snap, setSnap] = useState<TelemetrySnapshot>(empty);
  const [playing, setPlaying] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const snapRef = useRef(snap);

  useEffect(() => {
    snapRef.current = snap;
  }, [snap]);

  useEffect(() => {
    let cancelled = false;
    const pull = async () => {
      try {
        const response = await fetch("/api/osc", { cache: "no-store" });
        if (!response.ok) throw new Error("OSC bus unreachable.");
        const data = (await response.json()) as TelemetrySnapshot;
        if (!cancelled) {
          setSnap(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Telemetry failed.");
        }
      }
    };
    void pull();
    const id = setInterval(() => void pull(), 400);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      const current = snapRef.current;
      const beatHz = current.bpm / 60;
      const nextPhase = (current.beatPhase + beatHz * 0.12) % 1;
      void fetch("/api/osc/inject", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          beatPhase: nextPhase,
          bpm: current.bpm,
          fader: current.fader,
        }),
      });
    }, 120);
    return () => clearInterval(id);
  }, [playing]);

  const inject = (partial: { bpm?: number; fader?: number; beatPhase?: number }) => {
    void fetch("/api/osc/inject", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(partial),
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <NiagaraChamber
        cacheTime={snap.cacheTime}
        density={snap.density}
        bpm={snap.bpm}
        beatPhase={snap.beatPhase}
        cacheSeconds={niagaraCacheSeconds}
      />

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              BPM
              <Badge variant="outline">{snap.source}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="font-heading text-5xl tabular-nums text-primary">
              {snap.bpm.toFixed(1)}
            </p>
            <Slider
              value={[snap.bpm]}
              min={80}
              max={180}
              onValueChange={(value) =>
                inject({ bpm: Array.isArray(value) ? value[0] : value })
              }
              aria-label="Rehearsal BPM"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Fader / density</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="font-heading text-5xl tabular-nums text-[color:var(--signal)]">
              {snap.fader.toFixed(2)}
            </p>
            <Slider
              value={[snap.fader]}
              min={0}
              max={1}
              step={0.01}
              onValueChange={(value) =>
                inject({ fader: Array.isArray(value) ? value[0] : value })
              }
              aria-label="Rehearsal fader"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Beat phase</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="font-heading text-5xl tabular-nums">
              {snap.beatPhase.toFixed(2)}
            </p>
            <div className="flex gap-2">
              <Button
                variant={playing ? "default" : "outline"}
                onClick={() => setPlaying((value) => !value)}
              >
                {playing ? "Playing" : "Paused"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => inject({ beatPhase: 0, fader: 1, bpm: 140 })}
              >
                Drop
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>OSC log · 127.0.0.1:9000</CardTitle>
        </CardHeader>
        <CardContent>
          {snap.history.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No packets yet. Move a fader here, or start `npm run runtime` and send
              /rekordbox/bpm from Rekordbox.
            </p>
          ) : (
            <ul className="font-mono text-xs leading-6">
              {snap.history.slice(0, 12).map((message, index) => (
                <li key={`${message.receivedAt}-${index}`} className="flex gap-3">
                  <span className="text-muted-foreground">
                    {new Date(message.receivedAt).toISOString().slice(11, 23)}
                  </span>
                  <span className="text-primary">{message.address}</span>
                  <span>{message.args.map(String).join(" ")}</span>
                  <span className="text-muted-foreground">{message.source}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
