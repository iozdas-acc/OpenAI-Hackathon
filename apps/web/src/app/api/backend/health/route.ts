import { NextResponse } from "next/server";

const DEFAULT_API_URL = "http://localhost:8000";

export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;
  const startTime = performance.now();

  try {
    const response = await fetch(`${backendUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    const payload = (await response.json()) as { status?: string };
    const latencyMs = Math.round(performance.now() - startTime);

    return NextResponse.json(
      {
        backendUrl,
        checkedAt: new Date().toISOString(),
        latencyMs,
        payload,
        ok: response.ok,
        status: response.status,
      },
      { status: response.ok ? 200 : 503 },
    );
  } catch (error) {
    return NextResponse.json(
      {
        backendUrl,
        checkedAt: new Date().toISOString(),
        latencyMs: Math.round(performance.now() - startTime),
        payload: null,
        ok: false,
        status: 503,
        error: error instanceof Error ? error.message : "Backend probe failed.",
      },
      { status: 503 },
    );
  }
}
