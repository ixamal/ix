import { NextResponse } from "next/server";

import { probeOllama } from "@/lib/ollama";

export async function GET() {
  const status = await probeOllama();
  return NextResponse.json(status);
}
