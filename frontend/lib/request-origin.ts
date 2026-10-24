// TLS may terminate before Next.js. Pin the public origin in the server's
// environment rather than trusting forwarded headers supplied by a client.
export function isWorkspaceOrigin(
  request: Request,
  publicOrigin = process.env.TENDERLENS_PUBLIC_ORIGIN,
): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try {
    return origin === new URL(publicOrigin || request.url).origin;
  } catch {
    return false;
  }
}
