import {
  discoveryErrorResponse,
  latestTenderCatalog,
} from "@/lib/discovery-server";

export async function GET() {
  try {
    return Response.json(await latestTenderCatalog(), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return discoveryErrorResponse(error);
  }
}
