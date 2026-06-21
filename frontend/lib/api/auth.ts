import { apiFetch } from "./client";
import type { LoginRequest, LoginResponse, User } from "./types";

// POST /auth/login — sets the httpOnly session cookie on success.
// Throws ApiError; on 401 with detail "2FA code required" the error carries
// twoFactorRequired === true so the UI can reveal the TOTP field.
export function login(payload: LoginRequest): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

// POST /auth/logout — 204. Clears the session cookie server-side.
export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

// GET /auth/me — 200 User or 401 (ApiError.isUnauthenticated).
export function me(signal?: AbortSignal): Promise<User> {
  return apiFetch<User>("/auth/me", { signal });
}
