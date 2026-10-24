export async function GET() {
  try {
    const base = (
      process.env.TENDERLENS_API_URL ?? "http://127.0.0.1:8000"
    ).replace(/\/$/, "");
    const response = await fetch(`${base}/readyz`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    return Response.json(
      { ready: response.ok },
      {
        status: response.ok ? 200 : 503,
        headers: { "Cache-Control": "no-store" },
      },
    );
  } catch {
    return Response.json({ ready: false }, { status: 503 });
  }
}
