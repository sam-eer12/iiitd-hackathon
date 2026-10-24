import {
  discoveryErrorResponse,
  latestTenderCatalog,
} from "@/lib/discovery-server";

import { remoteWorkspace } from "@/lib/backend-proxy";
import { remoteCatalog } from "@/lib/remote-discovery";

export async function GET() {
  try {
    return Response.json(
      await (remoteWorkspace() ? remoteCatalog() : latestTenderCatalog()),
      {
        headers: { "Cache-Control": "no-store" },
      },
    );
  } catch (error) {
    return discoveryErrorResponse(error);
  }
}
