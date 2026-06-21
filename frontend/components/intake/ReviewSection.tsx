"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, listBids } from "@/lib/api";
import type { BidLineView } from "@/lib/api";
import {
  Button,
  Panel,
  PanelHeader,
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

  return (
    <Panel>
      <PanelHeader
        title="4 · Review bids"
        description={
          bids
            ? `${bids.length} bid line${bids.length === 1 ? "" : "s"} in round ${round}`
            : `Imported bid lines for round ${round}`
        }
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void load()}
            loading={loading}
          >
            Refresh
          </Button>
        }
      />

      {loading && (
        <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-ink-muted">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
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
          <p className="text-sm font-medium text-ink">No bids yet</p>
          <p className="mx-auto mt-1 max-w-sm text-sm text-ink-muted">
            Import a bid file above to populate this round.
          </p>
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
                  <TD className="font-medium">{b.supplier_id}</TD>
                  <TD className="text-ink-muted">{b.dc_id}</TD>
                  <TD className="text-ink-muted">{b.lot_id}</TD>
                  <TD className="text-ink-muted">{b.item_id}</TD>
                  <TD className="text-right tabular-nums">
                    {price == null ? (
                      <span className="text-ink-subtle">—</span>
                    ) : (
                      <>
                        {formatPrice(price)}{" "}
                        <span className="text-2xs text-ink-subtle">
                          {b.currency_code}
                        </span>
                      </>
                    )}
                  </TD>
                  <TD className="text-ink-muted">{basis || "—"}</TD>
                  <TD className="text-right tabular-nums text-ink-muted">
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
                  <TD className="text-ink-muted">
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
