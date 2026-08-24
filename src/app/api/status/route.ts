import { NextResponse } from "next/server";

import { getRigStatus } from "@/lib/status";

export async function GET() {
  const status = await getRigStatus();
  return NextResponse.json(status);
}
