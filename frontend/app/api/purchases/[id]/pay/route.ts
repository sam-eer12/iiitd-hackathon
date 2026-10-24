import { payPurchase } from "@/lib/purchase-server";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  return payPurchase(request, (await params).id);
}
