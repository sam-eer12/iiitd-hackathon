import { proxyCertificateRequest } from "@/lib/certificate-proxy";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)
  )
    return Response.json(
      { error: { message: "Invalid verification session." } },
      { status: 400 },
    );
  return proxyCertificateRequest(request, `/${id}/restart`);
}
