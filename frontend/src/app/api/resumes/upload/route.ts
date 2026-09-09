import { NextResponse } from "next/server";
import { backendFetch, getAuthToken } from "@/lib/backend";

export async function POST(request: Request) {
  const token = await getAuthToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const formData = await request.formData();

  const backendResponse = await backendFetch("/resumes/upload", token, {
    method: "POST",
    body: formData,
  });

  const data = await backendResponse.json();
  return NextResponse.json(data, { status: backendResponse.status });
}
