import "server-only";
import { isWorkspaceOrigin } from "./request-origin";

const headers = { "Cache-Control": "no-store" };
const unavailable = () =>
  Response.json(
    {
      error: {
        message:
          "Document verification is unavailable. Your certificate declarations remain unverified.",
      },
    },
    { status: 503, headers },
  );

export async function proxyCertificateRequest(request: Request, path = "") {
  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Bearer "))
    return Response.json(
      { error: { message: "Sign in to verify your documents." } },
      { status: 401, headers },
    );
  if (request.method !== "GET") {
    if (!isWorkspaceOrigin(request))
      return Response.json(
        {
          error: {
            message: "Use this workspace to start document verification.",
          },
        },
        { status: 403, headers },
      );
  }
  const body = request.method === "GET" ? undefined : await request.text();
  if (body && Buffer.byteLength(body, "utf8") > 8192)
    return Response.json(
      { error: { message: "Verification request is too large." } },
      { status: 413, headers },
    );
  try {
    const base = (
      process.env.TENDERLENS_API_URL ?? "http://127.0.0.1:8000"
    ).replace(/\/$/, "");
    const response = await fetch(
      `${base}/api/v1/certificate-verifications${path}`,
      {
        method: request.method,
        headers: {
          Authorization: authorization,
          "Content-Type": "application/json",
        },
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(90000),
      },
    );
    const payload = await response.json();
    return Response.json(payload, { status: response.status, headers });
  } catch {
    return unavailable();
  }
}
