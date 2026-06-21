// Typed fetch wrapper for the FastAPI backend.
//
// Rules enforced here, once, for every call:
//   - credentials: "include"  (the session lives in an httpOnly cookie)
//   - non-2xx responses throw a typed ApiError
//   - the 401 "2FA code required" case is surfaced as a distinct flag so the
//     login screen can reveal the TOTP field.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const API_PREFIX = "/api/v1";

// Backend signals "send me the TOTP code" with a 401 + this exact detail string.
const TWO_FACTOR_DETAIL = "2FA code required";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  // True when the backend is asking for a 2FA / TOTP code (401 + known detail).
  readonly twoFactorRequired: boolean;

  constructor(status: number, detail: string) {
    super(detail || `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.twoFactorRequired =
      status === 401 && detail.trim().toLowerCase() === TWO_FACTOR_DETAIL.toLowerCase();
  }

  // True for "not signed in" — but NOT the 2FA-required prompt, which is mid-login.
  get isUnauthenticated(): boolean {
    return this.status === 401 && !this.twoFactorRequired;
  }
}

// Best-effort extraction of FastAPI's { detail: ... } error shape.
async function extractDetail(res: Response): Promise<string> {
  try {
    const data = await res.clone().json();
    if (data && typeof data === "object" && "detail" in data) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail) && detail.length > 0) {
        // FastAPI validation errors: array of { msg, loc, ... }.
        const first = detail[0];
        if (first && typeof first === "object" && "msg" in first) {
          return String((first as { msg: unknown }).msg);
        }
      }
      if (detail != null) return JSON.stringify(detail);
    }
  } catch {
    // not JSON
  }
  return res.statusText || `HTTP ${res.status}`;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, signal } = options;

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
      method,
      // The session cookie must ride along on every request.
      credentials: "include",
      headers:
        body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
      cache: "no-store",
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    // Network / CORS / backend-down. Present as a 0-status ApiError.
    throw new ApiError(
      0,
      err instanceof Error ? err.message : "Network error — backend unreachable",
    );
  }

  if (!res.ok) {
    throw new ApiError(res.status, await extractDetail(res));
  }

  // 204 No Content (e.g. logout) — nothing to parse.
  if (res.status === 204) return undefined as T;

  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}
