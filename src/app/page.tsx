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

export default async function HallPage() {
  const rig = await getRigStatus();
  const oracle = rig.probes.find((probe) => probe.id === "ollama");
  const runtime = rig.probes.find((probe) => probe.id === "osc-runtime");
  const tools = rig.probes.find((probe) => probe.id === "local-tools");

  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col gap-5">
        <p className="text-[11px] tracking-[0.42em] text-primary uppercase">
          Primary planetary code base
        </p>
        <h1 className="font-heading max-w-3xl text-5xl leading-[1.05] text-balance sm:text-7xl">
          All things meet in victory here.
        </h1>
        <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
          IX is Valhalla for the live rig: Cursor as control plane, a local Ollama
          oracle kept off this git tree, Unreal Engine 5 Niagara caches, and bridges
          into DCC, DAW, and DJ tools — all on 127.0.0.1.
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

      <section className="grid gap-4 md:grid-cols-2">
        {halls.map((hall) => (
          <Link key={hall.id} href={hall.href} className="group">
            <Card className="h-full transition-colors group-hover:ring-primary/40">
              <CardHeader>
                <CardDescription className="tracking-[0.28em] uppercase">
                  {hall.epithet}
                </CardDescription>
                <CardTitle className="font-heading text-3xl">{hall.title}</CardTitle>
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
