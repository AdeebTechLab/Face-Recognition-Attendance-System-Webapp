import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
// Free backends (Render) can take ~50s to wake from sleep; the default Vercel limit is far shorter.
export const maxDuration = 60;

const BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
const API_KEY = process.env.BACKEND_API_KEY || "dev-biometric-secret-key-2026";

async function proxyRequest(req: NextRequest, { params }: { params: { path: string[] } }) {
  try {
    const targetPath = params.path.join("/");
    const search = req.nextUrl.search; // already includes leading "?"
    const url = `${BACKEND_URL}/api/${targetPath}${search}`;

    const headers: Record<string, string> = { "X-API-Key": API_KEY };
    const contentType = req.headers.get("content-type");
    if (contentType) headers["Content-Type"] = contentType;

    const init: RequestInit = { method: req.method, headers, cache: "no-store" };
    if (req.method !== "GET" && req.method !== "HEAD") {
      init.body = await req.text();
    }

    const upstream = await fetch(url, init);
    const body = await upstream.arrayBuffer();

    const responseHeaders: Record<string, string> = {
      "Content-Type": upstream.headers.get("Content-Type") || "application/json",
    };
    const disposition = upstream.headers.get("Content-Disposition");
    if (disposition) responseHeaders["Content-Disposition"] = disposition;

    return new NextResponse(body, { status: upstream.status, headers: responseHeaders });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown proxy error";
    return NextResponse.json(
      { detail: `Python backend unreachable (${BACKEND_URL}): ${message}` },
      { status: 502 }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
