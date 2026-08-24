import { NextResponse } from "next/server";

import { applyOscMessage, injectRehearsal, type OscSource } from "@/lib/osc-bus";
import { assertLoopbackHost } from "@/lib/safety";

function clientHost(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0]?.trim() || "127.0.0.1";
  return "127.0.0.1";
}

export async function POST(request: Request) {
  try {
    assertLoopbackHost(clientHost(request));
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Loopback only." },
      { status: 403 },
    );
  }

  const body = (await request.json().catch(() => null)) as {
    address?: string;
    args?: Array<number | string>;
    source?: OscSource;
    bpm?: number;
    fader?: number;
    beatPhase?: number;
  } | null;

  if (!body) {
    return NextResponse.json({ error: "Invalid JSON." }, { status: 400 });
  }

  if (body.address) {
    const snapshot = applyOscMessage({
      address: body.address,
      args: body.args ?? [],
      receivedAt: Date.now(),
      source: body.source ?? "loopback",
    });
    return NextResponse.json(snapshot);
  }

  const snapshot = injectRehearsal({
    bpm: body.bpm,
    fader: body.fader,
    beatPhase: body.beatPhase,
  });
  return NextResponse.json(snapshot);
}
