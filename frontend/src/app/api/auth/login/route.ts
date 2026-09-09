import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { AUTH_COOKIE_MAX_AGE_SECONDS, AUTH_COOKIE_NAME, BACKEND_URL } from "@/lib/backend";

export async function POST(request: Request) {
  const { email, password } = await request.json();

  // The backend's /auth/login uses OAuth2PasswordRequestForm, which expects
  // form-encoded fields named "username" and "password", not JSON.
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const backendResponse = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  const data = await backendResponse.json();

  if (!backendResponse.ok) {
    return NextResponse.json(data, { status: backendResponse.status });
  }

  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE_NAME, data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: AUTH_COOKIE_MAX_AGE_SECONDS,
  });

  return NextResponse.json({ success: true });
}
