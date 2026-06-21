import { apiFetch } from "./client";
import type { CreateRunRequest, RunDetail, RunSummary } from "./types";

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
