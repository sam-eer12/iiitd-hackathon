import type { NextRequest } from "next/server";
import {
  DiscoveryError,
  discoveryErrorResponse,
  pollDiscovery,
  publicJob,
  verifyJobSignature,
} from "@/lib/discovery-server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    if (
      !verifyJobSignature(
        id,
        request.cookies.get(`tenderlens-run-${id}`)?.value,
      )
    )
      throw new DiscoveryError(
        "This browser does not have access to that source run. Start discovery from Connected sources.",
        403,
      );
    const job = await pollDiscovery(id);
    return Response.json(
      { job: publicJob(job) },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return discoveryErrorResponse(error);
  }
}
