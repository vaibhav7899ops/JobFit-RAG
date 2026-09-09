import { NextResponse } from "next/server";
import { backendFetch, getAuthToken } from "@/lib/backend";

export async function GET() {
  const token = await getAuthToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const backendResponse = await backendFetch("/resumes", token);
  const data = await backendResponse.json();
  return NextResponse.json(data, { status: backendResponse.status });
}
