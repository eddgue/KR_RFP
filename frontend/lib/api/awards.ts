import { apiFetch } from "./client";
import type { AwardDetail, AwardSummary } from "./types";

// The post-award surface — view a cycle's FROZEN awards and inspect one (its
// baseline lines, the effective price per cell, and the versioned layer history).
// Read-only; the governed freeze lives in the alignment flow (`alignment.ts`).

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
