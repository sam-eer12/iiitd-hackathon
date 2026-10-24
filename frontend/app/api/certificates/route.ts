import { proxyCertificateRequest } from "@/lib/certificate-proxy";

export async function GET(request: Request) {
  return proxyCertificateRequest(request);
}

export async function POST(request: Request) {
  return proxyCertificateRequest(request);
}
