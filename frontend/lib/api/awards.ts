import { apiFetch } from "./client";
import type {
  AwardDetail,
  AwardSummary,
  FinalizeRunResponse,
  RecordAdjustmentBody,
  RecordAdjustmentResponse,
} from "./types";

// The post-award surface — view a cycle's FROZEN awards, inspect one (its baseline
// lines, the effective price per cell, and the versioned layer history), and record
// a governed append-only adjustment layer. The freeze itself lives in the alignment
// flow (`alignment.ts`).

const run = (slug: string) => `/runs/${encodeURIComponent(slug)}`;

// GET /runs/{slug}/awards -> AwardSummary[] (frozen awards, oldest first).
export function listAwards(
  slug: string,
  signal?: AbortSignal,
): Promise<AwardSummary[]> {
  return apiFetch<AwardSummary[]>(`${run(slug)}/awards`, { signal });
}

// GET /runs/{slug}/awards/{award_id} -> baseline + effective lines + version history.
export function getAward(
  slug: string,
  awardId: string,
  signal?: AbortSignal,
): Promise<AwardDetail> {
  return apiFetch<AwardDetail>(
    `${run(slug)}/awards/${encodeURIComponent(awardId)}`,
    { signal },
  );
}

// POST /runs/{slug}/awards/{award_id}/adjustments — append a versioned, governed
// adjustment layer; returns the new version_no + the regenerated document filename.
export function recordAdjustment(
  slug: string,
  awardId: string,
  body: RecordAdjustmentBody,
): Promise<RecordAdjustmentResponse> {
  return apiFetch<RecordAdjustmentResponse>(
    `${run(slug)}/awards/${encodeURIComponent(awardId)}/adjustments`,
    { method: "POST", body },
  );
}

// POST /runs/{slug}/finalize — terminal governed close-out of a run. Locks the run
// CLOSED (writes a CLOSED audit event) and returns the closing deliverables snapshot
// (the frozen award id + won / not-won supplier counts). Requires a FROZEN award;
// idempotent (re-finalizing a closed run returns the same summary, no second event).
export function finalizeRun(slug: string): Promise<FinalizeRunResponse> {
  return apiFetch<FinalizeRunResponse>(`${run(slug)}/finalize`, {
    method: "POST",
  });
}
