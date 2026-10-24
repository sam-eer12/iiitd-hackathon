import { NextRequest, NextResponse } from "next/server";
import {
  authorizeDiscovery,
  discoveryConfiguration,
  discoveryErrorResponse,
  jobSignature,
  publicJob,
  startDiscovery,
} from "@/lib/discovery-server";

export async function GET(request: NextRequest) {
  return NextResponse.json(discoveryConfiguration(request), {
    headers: { "Cache-Control": "no-store" },
  });
}

export async function POST(request: NextRequest) {
  try {
    authorizeDiscovery(request);
    const job = await startDiscovery();
    const response = NextResponse.json(
      { job: publicJob(job) },
      { status: 202 },
    );
    response.cookies.set(`tenderlens-run-${job.id}`, jobSignature(job.id), {
      httpOnly: true,
      sameSite: "strict",
      secure: request.nextUrl.protocol === "https:",
      path: "/api/discovery",
      maxAge: 86400,
    });
    return response;
  } catch (error) {
    return discoveryErrorResponse(error);
  }
}
