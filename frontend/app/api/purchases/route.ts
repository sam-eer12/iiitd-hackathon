import { proxyBackend } from "@/lib/backend-proxy";
import { startPurchase } from "@/lib/purchase-server";

export const GET = (request: Request) =>
  proxyBackend(request, "demo-purchases");
export const POST = startPurchase;
