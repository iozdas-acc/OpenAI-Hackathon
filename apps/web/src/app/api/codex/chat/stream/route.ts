const DEFAULT_API_URL = "http://localhost:8000";

export async function POST(request: Request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;

  const upstream = await fetch(`${backendUrl}/codex/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: await request.text(),
    cache: "no-store",
  });

  if (!upstream.body) {
    return new Response("Missing upstream stream body.", { status: 502 });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
