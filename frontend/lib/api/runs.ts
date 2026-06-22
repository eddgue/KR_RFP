import { apiFetch } from "./client";
import type {
  CreateRunRequest,
  RunDetail,
  RunSummary,
  Strategy,
  UpdateStrategyPayload,
} from "./types";

// GET /runs -> RunSummary[]
export function listRuns(signal?: AbortSignal): Promise<RunSummary[]> {
  return apiFetch<RunSummary[]>("/runs", { signal });
}

// POST /runs -> RunDetail (201)
export function createRun(payload: CreateRunRequest): Promise<RunDetail> {
  return apiFetch<RunDetail>("/runs", { method: "POST", body: payload });
}

// GET /runs/{slug} -> RunDetail
export function getRun(slug: string, signal?: AbortSignal): Promise<RunDetail> {
  return apiFetch<RunDetail>(`/runs/${encodeURIComponent(slug)}`, { signal });
}

// GET /runs/{slug}/strategy -> Strategy
export function getStrategy(slug: string, signal?: AbortSignal): Promise<Strategy> {
  return apiFetch<Strategy>(`/runs/${encodeURIComponent(slug)}/strategy`, { signal });
}

// PUT /runs/{slug}/strategy -> Strategy
export function updateStrategy(
  slug: string,
  payload: UpdateStrategyPayload,
): Promise<Strategy> {
  return apiFetch<Strategy>(`/runs/${encodeURIComponent(slug)}/strategy`, {
    method: "PUT",
    body: payload,
  });
}
