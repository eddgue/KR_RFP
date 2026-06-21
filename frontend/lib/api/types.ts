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
