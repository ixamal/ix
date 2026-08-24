import { TelemetryBoard } from "@/components/telemetry-board";

export default function TelemetryPage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-[11px] tracking-[0.42em] text-primary uppercase">
          Floor → Engine
        </p>
        <h1 className="font-heading text-4xl sm:text-5xl">Niagara cache scrub</h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
          Rehearse the live mapping without Unreal open. Rekordbox BPM, fader, and
          beat phase drive a 15-second sim cache the same way the OSC plugin will on
          Apple Silicon. Hardware adapters stay in ~/local_tools.
        </p>
      </header>
      <TelemetryBoard />
    </div>
  );
}
