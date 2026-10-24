import "server-only";

export const remoteWorkspace = () =>
  process.env.TENDERLENS_REMOTE_WORKSPACE === "true";

export async function backendFetch(path: string, init?: RequestInit) {
  const base = (
    process.env.TENDERLENS_API_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
  return fetch(`${base}/api/v1/${path}`, {
    ...init,
    cache: "no-store",
    signal: AbortSignal.timeout(20000),
  });
}

export async function proxyBackend(request: Request, path: string) {
  const headers = { "Cache-Control": "no-store" };
  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Bearer "))
    return Response.json(
      { error: { message: "Sign in to save your workspace." } },
      { status: 401, headers },
    );
  const origin = request.headers.get("origin");
  if (
    request.method !== "GET" &&
    origin &&
    origin !== new URL(request.url).origin
  )
    return Response.json(
      { error: { message: "Use this workspace to make changes." } },
      { status: 403, headers },
    );
  const body = request.method === "GET" ? undefined : await request.text();
  if (body && Buffer.byteLength(body) > 32768)
    return Response.json(
      { error: { message: "Request too large." } },
      { status: 413, headers },
    );
  try {
    const response = await backendFetch(path, {
      method: request.method,
      headers: {
        Authorization: authorization,
        "Content-Type": "application/json",
        ...(request.headers.get("idempotency-key")
          ? { "Idempotency-Key": request.headers.get("idempotency-key")! }
          : {}),
      },
      body: body || undefined,
    });
    return Response.json(await response.json(), {
      status: response.status,
      headers,
    });
  } catch {
    return Response.json(
      { error: { message: "Workspace storage is temporarily unavailable." } },
      { status: 503, headers },
    );
  }
}
