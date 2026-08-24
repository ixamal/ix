import { NextResponse } from "next/server";

import { getTelemetry } from "@/lib/osc-bus";

export async function GET() {
  return NextResponse.json(getTelemetry());
}
