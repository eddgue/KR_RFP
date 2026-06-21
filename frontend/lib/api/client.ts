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

// Error codes the structured envelope ({code, title, detail, ...}) can carry.
// The UI branches on these (e.g. gate_required keeps the user on the right step).
export type ApiErrorCode =
  | "gate_required"
  | "validation_error"
  | "not_found"
  | "unauthenticated"
  | string;

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  // Machine-readable code from the structured error envelope, when present.
  readonly code: ApiErrorCode | null;
  // True when the backend is asking for a 2FA / TOTP code (401 + known detail).
  readonly twoFactorRequired: boolean;

  constructor(status: number, detail: string, code: ApiErrorCode | null = null) {
    super(detail || `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
    this.twoFactorRequired =
      status === 401 && detail.trim().toLowerCase() === TWO_FACTOR_DETAIL.toLowerCase();
  }

  // True for "not signed in" — but NOT the 2FA-required prompt, which is mid-login.
  get isUnauthenticated(): boolean {
    return (
      (this.status === 401 || this.code === "unauthenticated") &&
      !this.twoFactorRequired
    );
  }

  // True when the action is blocked because a prerequisite step is incomplete.
  get isGateRequired(): boolean {
    return this.code === "gate_required";
  }
}

// Best-effort extraction of the error message + code from a non-2xx response.
// Handles both the structured envelope {code, title, detail, ...} and FastAPI's
// plain { detail: ... } shape.
async function extractError(
  res: Response,
): Promise<{ detail: string; code: ApiErrorCode | null }> {
  try {
    const data = await res.clone().json();
    if (data && typeof data === "object") {
      const obj = data as Record<string, unknown>;
      const code = typeof obj.code === "string" ? obj.code : null;
      const detail = obj.detail;
      if (typeof detail === "string") return { detail, code };
      if (Array.isArray(detail) && detail.length > 0) {
        // FastAPI validation errors: array of { msg, loc, ... }.
        const first = detail[0];
        if (first && typeof first === "object" && "msg" in first) {
          return { detail: String((first as { msg: unknown }).msg), code };
        }
      }
      // Structured envelope without a usable detail — fall back to its title.
      if (typeof obj.title === "string") return { detail: obj.title, code };
      if (detail != null) return { detail: JSON.stringify(detail), code };
    }
  } catch {
    // not JSON
  }
  return { detail: res.statusText || `HTTP ${res.status}`, code: null };
}

async function throwApiError(res: Response): Promise<never> {
  const { detail, code } = await extractError(res);
  throw new ApiError(res.status, detail, code);
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
    await throwApiError(res);
  }

  // 204 No Content (e.g. logout) — nothing to parse.
  if (res.status === 204) return undefined as T;

  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

interface UploadOptions {
  // Extra non-file form fields, sent alongside the file part.
  fields?: Record<string, string | number | boolean>;
  signal?: AbortSignal;
}

// Multipart upload. Builds a FormData body and lets the browser set the
// `Content-Type` (with its multipart boundary) — we must NOT set it ourselves,
// and the body is NOT JSON.stringify'd. Returns the parsed JSON response.
export async function apiUpload<T>(
  path: string,
  file: File,
  options: UploadOptions = {},
): Promise<T> {
  const { fields, signal } = options;

  const form = new FormData();
  form.append("file", file, file.name);
  if (fields) {
    for (const [key, value] of Object.entries(fields)) {
      form.append(key, String(value));
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
      method: "POST",
      credentials: "include",
      // No `Content-Type` header — the browser sets multipart/form-data + boundary.
      body: form,
      signal,
      cache: "no-store",
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(
      0,
      err instanceof Error ? err.message : "Network error — backend unreachable",
    );
  }

  if (!res.ok) {
    await throwApiError(res);
  }

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

// Pull a filename out of a Content-Disposition header, if the server sent one.
function filenameFromDisposition(header: string | null): string | null {
  if (!header) return null;
  // RFC 5987 form first: filename*=UTF-8''name.xlsx
  const star = /filename\*=(?:UTF-8'')?["']?([^"';]+)["']?/i.exec(header);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1]);
    } catch {
      return star[1];
    }
  }
  const plain = /filename=["']?([^"';]+)["']?/i.exec(header);
  return plain?.[1] ?? null;
}

// Authenticated binary download. Fetches with the session cookie, reads the
// response as a Blob, and triggers a browser download via a temporary object-URL
// anchor — using the server's filename when available, else `fallbackName`.
// On a non-2xx response this surfaces an ApiError (it does NOT navigate away),
// so callers can show the same inline error treatment as every other request.
export async function apiDownload(
  path: string,
  fallbackName: string,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(
      0,
      err instanceof Error ? err.message : "Network error — backend unreachable",
    );
  }

  if (!res.ok) {
    await throwApiError(res);
  }

  const blob = await res.blob();
  const filename =
    filenameFromDisposition(res.headers.get("content-disposition")) ??
    fallbackName;

  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    // Release the object URL on the next tick so the click has a chance to start.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}
