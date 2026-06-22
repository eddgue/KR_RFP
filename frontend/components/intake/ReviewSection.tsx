"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, listBids } from "@/lib/api";
import type { BidLineView } from "@/lib/api";
import {
  Button,
  Panel,
  StatusChip,
  Table,
  THead,
  TBody,
  TR,
  TH,
  TD,
} from "@/components/ui";
import { formatCount, formatPrice } from "@/lib/format";
import { Alert } from "./Alert";
import { StepHeader } from "./StepHeader";

export interface ReviewSectionProps {
  slug: string;
  round: number;
  // Bumping this forces a reload (e.g. after a successful import).
  refreshKey: number;
}

function validityTone(status: string) {
  const s = status.toLowerCase();
  if (/(valid|ok|complete|accepted)/.test(s)) return "green" as const;
  if (/(invalid|reject|expired|error)/.test(s)) return "amber" as const;
  return "slate" as const;
}

function BoolChip({ value }: { value: boolean }) {
  return (
    <StatusChip tone={value ? "green" : "slate"}>
      {value ? "Yes" : "No"}
    </StatusChip>
  );
}

// Step 4 — review the round's imported bid lines.
export function ReviewSection({ slug, round, refreshKey }: ReviewSectionProps) {
  const [bids, setBids] = useState<BidLineView[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listBids(slug, round);
      setBids(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail || "Could not load bids."
          : "Unexpected error loading bids.",
      );
    } finally {
      setLoading(false);
    }
  }, [slug, round]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  // Exception/quarantine queue: imported lines that still need a human decision
  // (not scoreable or not awardable) — surfaced so nothing is silently ignored.
  const quarantined = (bids ?? []).filter((b) => !b.is_scoreable || !b.is_awardable);
  const hasBids = Boolean(bids && bids.length > 0);

  return (
    <Panel>
      <StepHeader
        step={4}
        title="Review bids"
        description={
          bids
            ? `${bids.length} bid line${bids.length === 1 ? "" : "s"} in round ${round}`
            : `Imported bid lines for round ${round}`
        }
        state={hasBids ? "done" : "current"}
        actions={
          <>
            {hasBids && quarantined.length === 0 && (
              <StatusChip tone="green">Clean</StatusChip>
            )}
            {quarantined.length > 0 && (
              <StatusChip tone="amber">
                {quarantined.length} need review
              </StatusChip>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void load()}
              loading={loading}
            >
              Refresh
            </Button>
          </>
        }
      />

      {loading && (
        <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-text-muted">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-border-hairline border-t-brand-primary" />
          Loading bids…
        </div>
      )}

      {!loading && error && (
        <div className="px-5 py-5">
          <Alert tone="error">{error}</Alert>
          <Button
            variant="secondary"
            size="sm"
            className="mt-3"
            onClick={() => void load()}
          >
            Retry
          </Button>
        </div>
      )}

      {!loading && !error && bids && bids.length === 0 && (
        <div className="px-5 py-16 text-center">
          <p className="text-sm font-semibold text-text-strong">No bids yet</p>
          <p className="mx-auto mt-1 max-w-sm text-sm text-text-muted">
            Import a bid file above to populate this round.
          </p>
        </div>
      )}

      {!loading && !error && quarantined.length > 0 && (
        <div className="mx-5 mt-5 overflow-hidden rounded-card border border-danger/30 bg-danger-bg/50">
          <div className="flex items-center gap-2 border-b border-danger/20 px-4 py-2.5">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              className="text-danger"
              aria-hidden
            >
              <path d="M12 9v4M12 17h.01" />
              <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
            </svg>
            <span className="text-sm font-bold text-danger">Exception queue</span>
            <span className="rounded-control bg-danger/10 px-1.5 py-0.5 text-2xs font-extrabold tabular-nums text-danger">
              {quarantined.length}
            </span>
            <span className="ml-auto text-xs text-text-faint">
              Nothing is guessed — each needs a human decision
            </span>
          </div>
          <ul className="divide-y divide-danger/15">
            {quarantined.map((b) => (
              <li
                key={`q-${b.bid_line_id}`}
                className="flex items-start gap-3 px-4 py-2.5"
              >
                <StatusChip tone={!b.is_scoreable ? "gated" : "amber"}>
                  {!b.is_scoreable ? "Not scoreable" : "Not awardable"}
                </StatusChip>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-text-strong">
                    {b.supplier_id} · {b.dc_id} / {b.lot_id} / {b.item_id}
                  </p>
                  <p className="text-xs text-text-muted">
                    {b.incomplete_reason_code
                      ? `Reason: ${b.incomplete_reason_code}`
                      : `Validity: ${b.validity_status}`}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!loading && !error && bids && bids.length > 0 && (
        <Table>
          <THead>
            <TR>
              <TH>Supplier</TH>
              <TH>DC</TH>
              <TH>Lot</TH>
              <TH>Item</TH>
              <TH className="text-right">All-in / case</TH>
              <TH>Price basis</TH>
              <TH className="text-right">Min vol</TH>
              <TH>Validity</TH>
              <TH>Scoreable</TH>
              <TH>Awardable</TH>
              <TH>Incomplete reason</TH>
            </TR>
          </THead>
          <TBody>
            {bids.map((b) => {
              const price = b.submitted_all_in_case ?? b.fob_case;
              const basis = b.price_basis_resolved ?? b.price_basis;
              return (
                <TR key={b.bid_line_id}>
                  <TD className="font-semibold">{b.supplier_id}</TD>
                  <TD className="text-text-muted">{b.dc_id}</TD>
                  <TD className="text-text-muted">{b.lot_id}</TD>
                  <TD className="text-text-muted">{b.item_id}</TD>
                  <TD className="text-right tabular-nums">
                    {price == null ? (
                      <span className="text-text-subtle">—</span>
                    ) : (
                      <>
                        {formatPrice(price)}{" "}
                        <span className="text-2xs text-text-subtle">
                          {b.currency_code}
                        </span>
                      </>
                    )}
                  </TD>
                  <TD className="text-text-muted">{basis || "—"}</TD>
                  <TD className="text-right tabular-nums text-text-muted">
                    {formatCount(b.volume_minimum_cases)}
                  </TD>
                  <TD>
                    <StatusChip tone={validityTone(b.validity_status)}>
                      {b.validity_status}
                    </StatusChip>
                  </TD>
                  <TD>
                    <BoolChip value={b.is_scoreable} />
                  </TD>
                  <TD>
                    <BoolChip value={b.is_awardable} />
                  </TD>
                  <TD className="text-text-muted">
                    {b.incomplete_reason_code ?? "—"}
                  </TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
    </Panel>
  );
}
