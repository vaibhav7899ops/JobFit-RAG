import { NextResponse } from "next/server";
import { BACKEND_URL } from "@/lib/backend";

export async function GET(request: Request) {
  const { search } = new URL(request.url);

  const backendResponse = await fetch(`${BACKEND_URL}/jobs${search}`);
  const data = await backendResponse.json();
  return NextResponse.json(data, { status: backendResponse.status });
}
