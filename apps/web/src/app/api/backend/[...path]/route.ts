const DEFAULT_API_URL = "http://localhost:8000";

function buildUpstreamUrl(path: string[], requestUrl: string): string {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;
  const upstream = new URL(path.join("/"), backendUrl.endsWith("/") ? backendUrl : `${backendUrl}/`);
  const incoming = new URL(requestUrl);
  upstream.search = incoming.search;
  return upstream.toString();
}

async function forwardRequest(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const upstream = await fetch(buildUpstreamUrl(path, request.url), {
    method: request.method,
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
    cache: "no-store",
  });

  const contentType = upstream.headers.get("content-type") ?? "application/json";
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: {
      "Content-Type": contentType,
      "Cache-Control": "no-store",
    },
  });
}

export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  return forwardRequest(request, context);
}

export async function POST(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  return forwardRequest(request, context);
}
