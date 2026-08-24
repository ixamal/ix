"use client";

import { useEffect, useRef } from "react";

type NiagaraChamberProps = {
  cacheTime: number;
  density: number;
  bpm: number;
  beatPhase: number;
  cacheSeconds?: number;
};

export function NiagaraChamber({
  cacheTime,
  density,
  bpm,
  beatPhase,
  cacheSeconds = 15,
}: NiagaraChamberProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    let raf = 0;
    const blobs = Array.from({ length: 18 }, (_, i) => ({
      seed: i * 17.13,
      x: Math.random(),
      y: Math.random(),
    }));

    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "oklch(0.12 0.03 62)";
      ctx.fillRect(0, 0, width, height);

      const pulse = 0.55 + Math.sin(beatPhase * Math.PI * 2) * 0.45;
      const volume = 0.25 + density * 0.85;

      for (const blob of blobs) {
        const t = frame * 0.004 * (bpm / 126) + blob.seed + cacheTime;
        const x = (0.5 + Math.sin(t * 0.7) * 0.32 + (blob.x - 0.5) * 0.2) * width;
        const y = (0.62 + Math.cos(t * 0.45) * 0.22 + (blob.y - 0.5) * 0.15) * height;
        const radius = (40 + density * 90 + pulse * 24) * (0.6 + (blob.seed % 1));
        const gradient = ctx.createRadialGradient(x, y, 4, x, y, radius);
        gradient.addColorStop(0, `oklch(0.86 0.12 82 / ${0.22 * volume})`);
        gradient.addColorStop(0.35, `oklch(0.7 0.1 70 / ${0.16 * volume})`);
        gradient.addColorStop(1, "oklch(0.2 0.03 62 / 0)");
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      const playhead = (cacheTime / cacheSeconds) * width;
      ctx.strokeStyle = "oklch(0.78 0.11 200 / 0.85)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(playhead, 0);
      ctx.lineTo(playhead, height);
      ctx.stroke();

      frame += 1;
      raf = requestAnimationFrame(draw);
    };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.floor(rect.width * window.devicePixelRatio);
      canvas.height = Math.floor(rect.height * window.devicePixelRatio);
      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
    };

    resize();
    raf = requestAnimationFrame(draw);
    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [beatPhase, bpm, cacheSeconds, cacheTime, density]);

  return (
    <div className="relative overflow-hidden rounded-xl ring-1 ring-primary/20">
      <canvas ref={canvasRef} className="h-64 w-full sm:h-80" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between bg-gradient-to-t from-background/80 to-transparent px-4 py-3">
        <p className="font-mono text-[11px] tracking-wider text-primary">
          Niagara cache {cacheTime.toFixed(2)}s / {cacheSeconds}s
        </p>
        <p className="font-mono text-[11px] tracking-wider text-[color:var(--signal)]">
          density {density.toFixed(2)} · {bpm.toFixed(1)} BPM
        </p>
      </div>
    </div>
  );
}
