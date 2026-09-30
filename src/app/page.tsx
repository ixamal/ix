import type { Metadata } from "next";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { halls } from "@/lib/bridges";
import { getRigStatus } from "@/lib/status";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Alkalurops",
  description:
    "Real-time generative visual infrastructure. Zero latency. Driven by edge AI.",
};

const architecture = [
  {
    epithet: "ComfyUI · PyTorch",
    title: "Edge-optimized local AI",
    summary:
      "Quantized diffusion on the laptop: SDXL Turbo, LCM, Flux.1. Apple Metal Performance Shaders and TensorRT. Ultra-low latency frames at a small latent, then scale in the 3D engine.",
  },
  {
    epithet: "OSC · MIDI",
    title: "Zero-latency audio modulation",
    summary:
      "Live DAW stems and performance metrics over local UDP. Rekordbox, Traktor, Ableton on the loopback bus — amplitude, bands, and the booth, not a bounced movie.",
  },
  {
    epithet: "Syphon · NDI · UE5",
    title: "Real-time 3D compositing",
    summary:
      "Generative textures into Unreal Engine 5. Deterministic lighting and Niagara on top, so the stage stays safe when the model improvises.",
  },
];

const commercial = [
  {
    epithet: "Apache 2.0",
    title: "Community core",
    summary:
      "The research pipeline stays free and extensible. Fork it. Wire a node. Play a room.",
  },
  {
    epithet: "Later",
    title: "Standalone app",
    summary:
      "A future commercial desktop: one-click, no command line. Same engine, without the terminal.",
  },
  {
    epithet: "Venues",
    title: "Enterprise and venue",
    summary:
      "Turnkey stage solutions and custom nodes for venues, festivals, and TouchDesigner media servers.",
  },
];

export default async function HallPage() {
  const rig = await getRigStatus();
  const oracle = rig.probes.find((probe) => probe.id === "ollama");
  const runtime = rig.probes.find((probe) => probe.id === "osc-runtime");
  const tools = rig.probes.find((probe) => probe.id === "local-tools");

  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col gap-5">
        <p className="text-[11px] tracking-[0.42em] text-primary uppercase">
          Real-time generative visual infrastructure
        </p>
        <h1 className="font-heading max-w-3xl text-5xl leading-[1.05] text-balance sm:text-7xl">
          Alkalurops
        </h1>
        <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
          Zero latency. Driven by edge AI.
        </p>
        <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
          Live music visuals are either rigid and pre-rendered, or expensive
          enough to need a dedicated VJ. Alkalurops is an open-source research
          and engineering effort (Apache 2.0) to bring real-time generative AI
          visuals into the booth. A lightweight, edge-accelerated pipeline that
          runs beside memory-heavy DAWs and DJ software on one laptop, generating
          audio-reactive 3D environments and textures live, without audio
          dropouts or crashes.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/telemetry" className={cn(buttonVariants())}>
            Open telemetry
          </Link>
          <Link
            href="/oracle"
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            Probe the oracle
          </Link>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        <StatusChip
          label="Oracle"
          ok={oracle?.ok ?? false}
          detail={oracle?.ok ? "Ollama on loopback" : "Off-repo, currently dark"}
        />
        <StatusChip
          label="OSC runtime"
          ok={runtime?.ok ?? false}
          detail={runtime?.ok ? "UDP 9000" : "Start npm run runtime"}
        />
        <StatusChip
          label="local_tools"
          ok={tools?.ok ?? false}
          detail={tools?.ok ? "~/local_tools" : "Run the installer"}
        />
      </section>

      <section className="flex flex-col gap-4">
        <p className="text-[11px] tracking-[0.28em] text-muted-foreground uppercase">
          Ethos
        </p>
        <Card>
          <CardHeader>
            <CardDescription className="tracking-[0.28em] uppercase">
              The ninth planet
            </CardDescription>
            <CardTitle className="font-heading text-3xl">Ix</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm leading-6 text-muted-foreground sm:text-base">
            <p>
              In Frank Herbert&apos;s Dune, Ix is the ninth planet of the star
              Alkalurops, a world on the razor edge of a technological taboo. The
              commandment is &ldquo;Thou shalt not make a machine in the likeness
              of a human mind.&rdquo; Ix built the advanced hardware everyone
              else depended on and feared.
            </p>
            <p>
              The project name is an intentional, ironic statement. Modern AI
              carries a similar aura of anxiety. Alkalurops rejects the idea that
              models must replace or counterfeit human agency. It reclaims the
              technology as a real-time instrument: machine execution as a
              direct extension of the artist&apos;s live performance. The irony
              is ours — not a claim the books make for us.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="flex flex-col gap-4">
        <p className="text-[11px] tracking-[0.28em] text-muted-foreground uppercase">
          Architecture
        </p>
        <div className="grid gap-4 md:grid-cols-3">
          {architecture.map((beat) => (
            <Card key={beat.title} className="h-full">
              <CardHeader>
                <CardDescription className="tracking-[0.28em] uppercase">
                  {beat.epithet}
                </CardDescription>
                <CardTitle className="font-heading text-3xl">
                  {beat.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                {beat.summary}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <p className="text-[11px] tracking-[0.28em] text-muted-foreground uppercase">
          Open core
        </p>
        <div className="grid gap-4 md:grid-cols-3">
          {commercial.map((beat) => (
            <Card key={beat.title} className="h-full">
              <CardHeader>
                <CardDescription className="tracking-[0.28em] uppercase">
                  {beat.epithet}
                </CardDescription>
                <CardTitle className="font-heading text-3xl">
                  {beat.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                {beat.summary}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <p className="text-[11px] tracking-[0.28em] text-muted-foreground uppercase">
          Community
        </p>
        <Card>
          <CardHeader>
            <CardDescription className="tracking-[0.28em] uppercase">
              Apache 2.0
            </CardDescription>
            <CardTitle className="font-heading text-3xl">
              Open, accessible, resilient
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4 text-sm leading-6 text-muted-foreground sm:text-base">
            <p>
              Live performance tools should be open, accessible, and resilient.
              The core is Apache 2.0. Artists and developers who want generative
              visuals in the booth — without a rented VJ stack — are invited to
              collaborate.
            </p>
            <Link
              href="https://github.com/ixamal/ix"
              className={cn(buttonVariants({ variant: "outline" }), "w-fit")}
            >
              github.com/ixamal/ix
            </Link>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {halls.map((hall) => (
          <Link key={hall.id} href={hall.href} className="group">
            <Card className="h-full transition-colors group-hover:ring-primary/40">
              <CardHeader>
                <CardDescription className="tracking-[0.28em] uppercase">
                  {hall.epithet}
                </CardDescription>
                <CardTitle className="font-heading text-3xl">
                  {hall.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                {hall.summary}
              </CardContent>
            </Card>
          </Link>
        ))}
      </section>
    </div>
  );
}

function StatusChip({
  label,
  ok,
  detail,
}: {
  label: string;
  ok: boolean;
  detail: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-card px-4 py-3 ring-1 ring-primary/15">
      <div>
        <p className="text-[11px] tracking-[0.22em] text-muted-foreground uppercase">
          {label}
        </p>
        <p className="text-sm">{detail}</p>
      </div>
      <Badge variant={ok ? "default" : "outline"}>{ok ? "live" : "dark"}</Badge>
    </div>
  );
}
