import { cookies } from "next/headers";

export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const AUTH_COOKIE_NAME = "jobfit_token";

// Mirrors the backend's ACCESS_TOKEN_EXPIRE_MINUTES (24 hours), in seconds.
export const AUTH_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24;

export async function getAuthToken(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(AUTH_COOKIE_NAME)?.value;
}

/** Forwards a request to the FastAPI backend with the caller's bearer token attached. */
export async function backendFetch(path: string, token: string, init: RequestInit = {}) {
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}
