import { apiDownload, apiFetch, apiUpload } from "./client";
import type {
  BidImportMode,
  BidImportResponse,
  BidLineView,
  RunFile,
  SetupResult,
  TemplateResult,
} from "./types";

// --- Run files -------------------------------------------------------------

// GET /runs/{slug}/files -> RunFile[]
export function listRunFiles(
  slug: string,
  signal?: AbortSignal,
): Promise<RunFile[]> {
  return apiFetch<RunFile[]>(
    `/runs/${encodeURIComponent(slug)}/files`,
    { signal },
  );
}

// GET /runs/{slug}/files/{name} -> .xlsx attachment (browser download).
export function downloadRunFile(slug: string, name: string): Promise<void> {
  return apiDownload(
    `/runs/${encodeURIComponent(slug)}/files/${encodeURIComponent(name)}`,
    name,
  );
}

// GET /runs/{slug}/archive -> .zip attachment of the whole run folder.
export function downloadRunArchive(slug: string): Promise<void> {
  return apiDownload(
    `/runs/${encodeURIComponent(slug)}/archive`,
    `${slug}.zip`,
  );
}

// --- Setup -----------------------------------------------------------------

// POST /runs/{slug}/setup (multipart `file`) -> { cycle_id, kanban }
export function uploadSetup(slug: string, file: File): Promise<SetupResult> {
  return apiUpload<SetupResult>(
    `/runs/${encodeURIComponent(slug)}/setup`,
    file,
  );
}

// --- Bid template ----------------------------------------------------------

// POST /runs/{slug}/rounds/{round}/template -> { filename, kanban }
export function generateTemplate(
  slug: string,
  round: number,
): Promise<TemplateResult> {
  return apiFetch<TemplateResult>(
    `/runs/${encodeURIComponent(slug)}/rounds/${round}/template`,
    { method: "POST" },
  );
}

// --- Bid import ------------------------------------------------------------

export interface ImportBidsArgs {
  run: string;
  round: number;
  mode: BidImportMode;
  // strict ⇒ always written. flexible+false ⇒ dry-run proposal, nothing written.
  // flexible+true ⇒ confirm a previously proposed mapping and write.
  confirm: boolean;
  file: File;
}

// POST /bids/import (multipart: file; form fields run, round, mode, confirm).
// Returns BidImportResult (ingested) or BidImportProposal (dry run) — narrow
// with isBidImportProposal().
export function importBids(args: ImportBidsArgs): Promise<BidImportResponse> {
  const { run, round, mode, confirm, file } = args;
  return apiUpload<BidImportResponse>("/bids/import", file, {
    fields: { run, round, mode, confirm },
  });
}

// --- Bid review ------------------------------------------------------------

// GET /bids?run={slug}&round={round} -> BidLineView[]
export function listBids(
  run: string,
  round: number,
  signal?: AbortSignal,
): Promise<BidLineView[]> {
  const params = new URLSearchParams({ run, round: String(round) });
  return apiFetch<BidLineView[]>(`/bids?${params.toString()}`, { signal });
}
