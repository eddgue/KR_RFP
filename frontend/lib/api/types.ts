// Hand-written TS types matching the FastAPI backend contract.
// Kept in lockstep with the documented endpoints; replaced by generated types at
// the OpenAPI codegen step (see package.json `gen:api`).

export interface User {
  id: string;
  username: string;
  totp_enabled: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
  totp_code?: string;
}

export interface LoginResponse {
  user: User;
}

// Summary row returned by GET /runs.
export interface RunSummary {
  slug: string;
  commodity: string;
  label: string;
  rehearsal: boolean;
  stage: string;
}

// The four fixed kanban buckets, in display order.
export const KANBAN_BUCKETS = [
  "Done",
  "Doing",
  "Next",
  "Waiting on you",
] as const;

export type KanbanBucket = (typeof KANBAN_BUCKETS)[number];

// A card may be a plain string or an object; the contract shows arrays of items,
// so we keep it permissive but typed.
export type KanbanCard =
  | string
  | {
      id?: string;
      title?: string;
      label?: string;
      [key: string]: unknown;
    };

export type Kanban = Record<KanbanBucket, KanbanCard[]>;

// Full detail returned by POST /runs and GET /runs/{slug}.
export interface RunDetail extends RunSummary {
  kanban: Kanban;
}

export interface CreateRunRequest {
  commodity: string;
  label: string;
  rehearsal?: boolean;
}

// ---------------------------------------------------------------------------
// Bid-intake contract (run files, setup, templates, bid import, bid review).
// Field names mirror the backend exactly.
// ---------------------------------------------------------------------------

// A file in a run folder. GET /runs/{slug}/files -> RunFile[].
export interface RunFile {
  name: string;
  kind: "input" | "output";
  size_bytes: number;
  modified: string; // ISO timestamp
}

// Server returns kanban buckets as a loose Record<string, string[]>; we keep the
// raw shape from these endpoints and normalize to Kanban when rendering.
export type KanbanResponse = Record<string, string[]>;

// POST /runs/{slug}/setup (multipart `file`).
export interface SetupResult {
  cycle_id: string;
  kanban: KanbanResponse;
}

// POST /runs/{slug}/rounds/{round}/template.
export interface TemplateResult {
  filename: string;
  kanban: KanbanResponse;
}

export type BidImportMode = "strict" | "flexible";

export type MappingConfidence = "high" | "medium" | "low";

// A single field -> column mapping within a flexible-import proposal.
export interface MappingEntry {
  field: string;
  column_index: number;
  source_header: string;
  basis: string;
  confidence: MappingConfidence;
}

// Returned on a flexible import with confirm=false: a dry-run proposal that the
// user reviews before anything is written.
export interface MappingProposalView {
  sheet_name: string;
  header_row: number;
  mappings: Record<string, MappingEntry>;
  ambiguities: string[];
  is_confident: boolean;
  summary: string;
}

// POST /bids/import — strict, or flexible+confirm=true.
export interface BidImportResult {
  ingested: number;
  kanban: KanbanResponse;
}

// POST /bids/import — flexible+confirm=false (nothing written).
export interface BidImportProposal {
  proposal: MappingProposalView;
}

// The two possible POST /bids/import payloads.
export type BidImportResponse = BidImportResult | BidImportProposal;

// Narrowing helper for the discriminated import response.
export function isBidImportProposal(
  res: BidImportResponse,
): res is BidImportProposal {
  return "proposal" in res;
}

// A scored/aligned bid line. GET /bids?run=&round= -> BidLineView[].
export interface BidLineView {
  bid_line_id: string;
  supplier_id: string;
  dc_id: string;
  lot_id: string;
  item_id: string;
  tf_id: string;
  fiscal_period_id: string | null;
  currency_code: string;
  price_basis: string;
  submitted_all_in_case: number | null;
  fob_case: number | null;
  price_basis_resolved: string | null;
  volume_minimum_cases: number | null;
  transit_days: number | null;
  validity_status: string;
  is_scoreable: boolean;
  is_awardable: boolean;
  incomplete_reason_code: string | null;
}
