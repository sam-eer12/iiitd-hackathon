import { proxyBackend } from "@/lib/backend-proxy";
export const GET = (request: Request) => proxyBackend(request, "profile");
export const PUT = (request: Request) => proxyBackend(request, "profile");
