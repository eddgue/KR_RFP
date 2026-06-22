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
  // True once setup has been ingested (a cycle exists) — the durable signal the intake UI uses to
  // unlock the post-setup steps, independent of any generated file.
  has_cycle: boolean;
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

// ---------------------------------------------------------------------------
// Alignment / scenario contract: sealed analyses, the seven lenses (A-G), the
// per-cell competitive grid, and the governed award freeze. Field names mirror
// the backend `app.domain.eng.read` + `app.api.v1.runs` views exactly.
// ---------------------------------------------------------------------------

// One sealed eng.analysis_run. GET /runs/{slug}/analysis -> AnalysisSummary[].
export interface AnalysisSummary {
  // 1-based ordinal among the cycle's sealed runs (oldest = 1).
  version: number;
  analysis_run_id: string;
  round_number: number;
  engine_version: string;
  sealed_at: string; // ISO timestamp
}

// POST /runs/{slug}/rounds/{round}/analysis — seals eng.* + writes the workbook.
export interface RunAnalysisResponse {
  version: number;
  analysis_run_id: string;
  round_number: number;
  sealed_at: string;
  scenario_count: number;
  filename: string;
}

// One lens rolled up. GET /runs/{slug}/analysis/{id}/scenarios -> [].
export interface ScenarioComparisonRow {
  code: string; // lens code A-G
  label: string;
  description: string;
  total_spend: number;
  delta_vs_a: number; // spend Δ vs lens A (the lowest-cost benchmark)
  savings_vs_incumbent_pct: number; // fraction (0.05 = 5%)
  savings_vs_stly_pct: number; // fraction vs the synthetic prior-year proxy
  supplier_count: number;
  cell_count: number;
  cap_breach_count: number;
  is_recommended: boolean; // true for lens B (the default recommendation)
}

// One supplier's competitive line within a cell.
export interface SupplierCell {
  name: string;
  price_per_case: number | null;
  is_min: boolean; // lowest priced bid in the cell
  is_incumbent: boolean;
  is_recommended: boolean; // this lens awarded this supplier the cell
  rec_score: number | null; // RecScore 0-100
  volume_share: number; // this lens's awarded share (fraction; 0 if not awarded)
}

// The supplier a lens awarded a cell (+ B-only rec_type reason).
export interface SupplierCellRef {
  supplier: string;
  rec_type: string; // B reason label ("Lowest cost" / …); "" for other lenses
  price: number | null;
}

// One (DC × lot × item × TF) cell resolved to names + the competitive picture.
export interface ScenarioDetailCell {
  dc: string;
  lot: string;
  item: string;
  tf: string;
  volume: number;
  baseline_price: number; // incumbent-routing baseline $/case
  min_price: number | null;
  incumbent_supplier: string;
  suppliers: SupplierCell[];
  recommended: SupplierCellRef | null;
}

export interface ScenarioSavingsSummary {
  total_spend: number;
  savings_vs_incumbent: number; // dollars
  savings_vs_incumbent_pct: number; // fraction
  savings_vs_stly: number;
  savings_vs_stly_pct: number;
}

// One lens cell-by-cell. GET /runs/{slug}/analysis/{id}/scenarios/{code}.
export interface ScenarioDetail {
  code: string;
  label: string;
  description: string;
  is_recommended: boolean;
  savings: ScenarioSavingsSummary;
  cells: ScenarioDetailCell[];
}

// POST /runs/{slug}/awards/freeze.
export interface FreezeAwardRequest {
  analysis_run_id: string;
  scenario_code: string;
  award_code: string;
}

export interface FreezeAwardResponse {
  award_id: string;
  scenario_code: string;
}

// ---------------------------------------------------------------------------
// Post-award contract: frozen awards + their versioned adjustment layers.
// GET /runs/{slug}/awards and /runs/{slug}/awards/{id} (app.domain.awd.read).
// ---------------------------------------------------------------------------

// One frozen award. GET /runs/{slug}/awards -> AwardSummary[].
export interface AwardSummary {
  award_id: string;
  award_code: string;
  scenario_code: string;
  frozen_at: string; // ISO timestamp
  frozen_by: string;
  line_count: number;
  latest_version: number; // highest adjustment version (0 = baseline only)
}

// One awarded cell — names (D23) + frozen baseline, effective price, and delta.
// The cell-key ids identify the cell exactly (used when recording an adjustment).
export interface AwardLineView {
  dc_id: string;
  lot_id: string;
  tf_id: string;
  supplier_id: string;
  dc: string;
  lot: string;
  tf: string;
  supplier: string;
  volume_share: number; // fraction (0–1)
  frozen_price: number;
  effective_price: number; // baseline overlaid by every layer
  delta: number; // effective_price − frozen_price
}

// One cell repriced by a post-award adjustment. POST .../adjustments body item.
export interface AdjustmentLineChange {
  dc_id: string;
  lot_id: string;
  tf_id: string;
  supplier_id: string;
  new_price: number; // must be > 0
}

// POST /runs/{slug}/awards/{award_id}/adjustments — append a versioned layer.
export interface RecordAdjustmentBody {
  adjustment_type: string;
  effective_date: string; // ISO date (YYYY-MM-DD)
  reason: string;
  changes: AdjustmentLineChange[]; // at least one
}

// The recorded layer's new version + the regenerated post-award document filename.
export interface RecordAdjustmentResponse {
  award_id: string;
  version_no: number;
  filename: string;
}

// One row of the version history (v0 FROZEN → vN layers).
export interface AwardVersionView {
  version_no: number;
  adjustment_type: string;
  effective_date: string; // ISO date (YYYY-MM-DD)
  reason: string;
  created_at: string; // ISO timestamp
  created_by: string;
  n_lines: number;
}

// One frozen award inspected. GET /runs/{slug}/awards/{award_id}.
export interface AwardDetail {
  award_id: string;
  award_code: string;
  scenario_code: string;
  frozen_at: string;
  frozen_by: string;
  latest_version: number;
  lines: AwardLineView[];
  versions: AwardVersionView[];
}

// POST /runs/{slug}/finalize — terminal governed close-out. Locks the run CLOSED
// (a CLOSED audit event lands) and surfaces the closing deliverables: award notices
// (won suppliers) + rejection notices (not-won suppliers). Ids + counts only; the
// notices render on request (nothing persisted). Idempotent; requires a FROZEN award.
export interface FinalizeRunResponse {
  closed: boolean;
  award_id: string;
  won_suppliers: number;
  not_won_suppliers: number;
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
