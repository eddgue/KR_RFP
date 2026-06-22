import { apiFetch } from "./client";
import type {
  AnalysisSummary,
  FreezeAwardRequest,
  FreezeAwardResponse,
  RunAnalysisResponse,
  ScenarioComparisonRow,
  ScenarioDetail,
} from "./types";

// The web alignment / scenario slice — run a round's analysis, list the sealed
// runs, compare the seven lenses, inspect one lens cell-by-cell, and freeze a
// chosen lens. Each call wraps a `/runs/{slug}/…` endpoint (see app.api.v1.runs).

const run = (slug: string) => `/runs/${encodeURIComponent(slug)}`;

// POST /runs/{slug}/rounds/{round}/analysis -> seals eng.* + writes the workbook.
export function runAnalysis(
  slug: string,
  round: number,
): Promise<RunAnalysisResponse> {
  return apiFetch<RunAnalysisResponse>(`${run(slug)}/rounds/${round}/analysis`, {
    method: "POST",
  });
}

// GET /runs/{slug}/analysis -> AnalysisSummary[] (sealed runs, oldest first).
export function listAnalyses(
  slug: string,
  signal?: AbortSignal,
): Promise<AnalysisSummary[]> {
  return apiFetch<AnalysisSummary[]>(`${run(slug)}/analysis`, { signal });
}

// GET /runs/{slug}/analysis/{id}/scenarios -> the seven lenses side by side.
export function getScenarioComparison(
  slug: string,
  analysisRunId: string,
  signal?: AbortSignal,
): Promise<ScenarioComparisonRow[]> {
  return apiFetch<ScenarioComparisonRow[]>(
    `${run(slug)}/analysis/${encodeURIComponent(analysisRunId)}/scenarios`,
    { signal },
  );
}

// GET /runs/{slug}/analysis/{id}/scenarios/{code} -> one lens, cell-by-cell.
export function getScenarioDetail(
  slug: string,
  analysisRunId: string,
  scenarioCode: string,
  signal?: AbortSignal,
): Promise<ScenarioDetail> {
  return apiFetch<ScenarioDetail>(
    `${run(slug)}/analysis/${encodeURIComponent(analysisRunId)}/scenarios/${encodeURIComponent(scenarioCode)}`,
    { signal },
  );
}

// PATCH /runs/{slug}/analysis/{id} -> name a sealed version (savepoint, NOT a freeze).
export function nameVersion(
  slug: string,
  analysisRunId: string,
  label: string,
): Promise<AnalysisSummary> {
  return apiFetch<AnalysisSummary>(
    `${run(slug)}/analysis/${encodeURIComponent(analysisRunId)}`,
    { method: "PATCH", body: { label } },
  );
}

// POST /runs/{slug}/awards/freeze -> { award_id, scenario_code }.
export function freezeAward(
  slug: string,
  body: FreezeAwardRequest,
): Promise<FreezeAwardResponse> {
  return apiFetch<FreezeAwardResponse>(`${run(slug)}/awards/freeze`, {
    method: "POST",
    body,
  });
}
