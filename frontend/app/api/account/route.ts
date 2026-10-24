import { proxyBackend } from "@/lib/backend-proxy";
export const PUT = (request: Request) => proxyBackend(request, "me");
