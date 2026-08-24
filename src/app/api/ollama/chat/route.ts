import { NextResponse } from "next/server";

import { chatOllama } from "@/lib/ollama";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as {
    model?: string;
    prompt?: string;
  } | null;

  const prompt = body?.prompt?.trim() ?? "";
  const model = body?.model?.trim() ?? "";
  if (!prompt || !model) {
    return NextResponse.json(
      { error: "Both model and prompt are required." },
      { status: 400 },
    );
  }

  try {
    const result = await chatOllama({ model, prompt });
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Ollama chat failed.";
    return NextResponse.json({ error: message }, { status: 503 });
  }
}
