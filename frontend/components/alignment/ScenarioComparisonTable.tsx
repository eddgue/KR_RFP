"use client";

import {
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
import { cn } from "@/lib/cn";
import { formatCount, formatMoney, formatPercent } from "@/lib/format";
import type { ScenarioComparisonRow } from "@/lib/api";

// The seven lenses A–G side by side — the "which scenario" decision surface. Numbers
// are identical to the alignment workbook's Scenario Comparison tab (same gather).
// B is flagged Recommended; A is the lowest-cost benchmark Δ is measured against.
// Each lens reshapes the award matrix below; selecting one drives the cell-by-cell
// detail. Below ~1100px the table scrolls horizontally (never reflows to cards) so
// the lens-vs-lens read stays intact — DC stays the locked primary grouping there.
export function ScenarioComparisonTable({
  rows,
  selectedCode,
  onSelect,
}: {
  rows: ScenarioComparisonRow[];
  selectedCode: string | null;
  onSelect: (code: string) => void;
}) {
  // §B5 — every rollup reflects the set actually shown, never a stale full count.
  const shown = rows.length;
  const capBreaches = rows.filter((r) => r.cap_breach_count > 0).length;

  return (
    <Panel>
      <PanelHeader
        title={
          <span className="font-display text-base font-bold text-text-strong">
            Scenario lenses
          </span>
        }
        description="Each lens A–G reshapes the award below. Lens B is the recommended default; A is the lowest-cost benchmark. Select a lens to inspect it cell by cell."
        actions={
          <span className="text-2xs font-semibold text-text-subtle">
            {shown} {shown === 1 ? "lens" : "lenses"}
            {capBreaches > 0 && (
              <>
                {" · "}
                <span className="text-danger">
                  {capBreaches} over stated capacity
                </span>
              </>
            )}
          </span>
        }
      />
      <Table className="min-w-[1100px]">
        <THead>
          <TR>
            <TH>Lens</TH>
            <TH className="text-right">Spend</TH>
            <TH className="text-right">Δ vs A</TH>
            <TH className="text-right">Save vs incumbent</TH>
            <TH className="text-right">
              Save vs STLY{" "}
              <StatusChip tone="modeled" className="ml-1 align-middle">
                modeled
              </StatusChip>
            </TH>
            <TH className="text-right">Suppliers</TH>
            <TH className="text-right">Cells</TH>
            <TH className="text-right">Capacity</TH>
          </TR>
        </THead>
        <TBody>
          {rows.map((r) => {
            const selected = r.code === selectedCode;
            const overCap = r.cap_breach_count > 0;
            return (
              <TR
                key={r.code}
                onClick={() => onSelect(r.code)}
                className={cn(
                  selected && "bg-accent-soft ring-1 ring-inset ring-brand-primary/30",
                )}
              >
                <TD>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "flex h-6 w-6 shrink-0 items-center justify-center rounded-control font-display text-2xs font-extrabold",
                        selected
                          ? "bg-brand-primary text-white"
                          : r.is_recommended
                            ? "bg-success-bg text-success"
                            : "bg-surface-muted text-text-muted",
                      )}
                    >
                      {r.code}
                    </span>
                    <span className="font-semibold text-text-strong">{r.label}</span>
                    {r.is_recommended && (
                      <StatusChip tone="green">Recommended</StatusChip>
                    )}
                  </div>
                </TD>
                <TD className="text-right font-display font-semibold tabular-nums text-text-strong">
                  {formatMoney(r.total_spend)}
                </TD>
                <TD className="text-right tabular-nums text-text-muted">
                  {r.delta_vs_a === 0 ? "—" : formatMoney(r.delta_vs_a)}
                </TD>
                <TD className="text-right tabular-nums font-semibold text-success">
                  {formatPercent(r.savings_vs_incumbent_pct)}
                </TD>
                <TD className="text-right tabular-nums text-text-faint">
                  {formatPercent(r.savings_vs_stly_pct)}
                </TD>
                <TD className="text-right tabular-nums text-text">
                  {formatCount(r.supplier_count)}
                </TD>
                <TD className="text-right tabular-nums text-text">
                  {formatCount(r.cell_count)}
                </TD>
                <TD className="text-right tabular-nums">
                  {overCap ? (
                    <StatusChip tone="gated">
                      {r.cap_breach_count} over
                    </StatusChip>
                  ) : (
                    <span className="text-text-faint">Feasible</span>
                  )}
                </TD>
              </TR>
            );
          })}
        </TBody>
      </Table>
    </Panel>
  );
}
