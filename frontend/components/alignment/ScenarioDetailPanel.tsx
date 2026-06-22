"use client";

import { useState } from "react";
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
import { cn } from "@/lib/cn";
import { formatCount, formatMoney, formatPercent, formatPrice } from "@/lib/format";
import type { ScenarioDetailCell } from "@/lib/api";
import type { ScenarioDetail } from "@/lib/api";

// One lens inspected cell-by-cell — the workbench matrix. DC is the locked primary
// grouping; the matrix scrolls horizontally below ~1100px and never reflows to
// cards. Headline savings, a scenario-level capacity-feasibility indicator, and the
// governed freeze action sit above the per-(DC × lot × item × TF) competitive grid.
// Each cell row expands to the full supplier picture (price, RecScore, share, flags).
export function ScenarioDetailPanel({
  detail,
  frozenAwardId,
  onFreeze,
  readOnly = false,
  capBreachCount = null,
}: {
  detail: ScenarioDetail;
  frozenAwardId: string | null;
  onFreeze: () => void;
  /** Viewing a sealed/historic analysis — governed freeze is disabled. */
  readOnly?: boolean;
  /** Stated-capacity breach count for this lens (from the comparison rollup, E-38).
   *  null when the analysis doesn't expose it; the indicator is then hidden. */
  capBreachCount?: number | null;
}) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const toggle = (i: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });

  const s = detail.savings;

  // Scenario-level capacity feasibility (stated-capacity, E-38 — distinct from
  // concentration). Sourced from the comparison rollup for THIS lens, so it can never
  // disagree with the per-lens row above it (§B5).
  const showCap = capBreachCount != null;
  const capFeasible = (capBreachCount ?? 0) === 0;

  return (
    <Panel>
      <PanelHeader
        title={
          <span className="flex flex-wrap items-center gap-2">
            <span className="font-display text-base font-bold text-text-strong">
              Lens {detail.code} — {detail.label}
            </span>
            {detail.is_recommended && <StatusChip tone="green">Recommended</StatusChip>}
            {showCap && (
              <StatusChip tone={capFeasible ? "green" : "gated"}>
                {capFeasible
                  ? "Feasible vs stated capacity"
                  : `Over stated capacity · ${capBreachCount} ${capBreachCount === 1 ? "cell" : "cells"}`}
              </StatusChip>
            )}
          </span>
        }
        description={detail.description}
        actions={
          frozenAwardId ? (
            <StatusChip tone="frozen">Frozen · {frozenAwardId.slice(0, 8)}</StatusChip>
          ) : (
            <Button size="sm" onClick={onFreeze} disabled={readOnly}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden>
                <rect x="5" y="11" width="14" height="9" rx="2" />
                <path d="M8 11V8a4 4 0 0 1 8 0v3" />
              </svg>
              Freeze award
            </Button>
          )
        }
      />

      <div className="grid grid-cols-2 gap-px bg-border-hairline sm:grid-cols-4">
        <Stat label="Total spend" value={formatMoney(s.total_spend)} />
        <Stat
          label="Save vs incumbent"
          value={formatMoney(s.savings_vs_incumbent)}
          sub={formatPercent(s.savings_vs_incumbent_pct)}
          positive
        />
        <Stat
          label="Save vs STLY"
          value={formatMoney(s.savings_vs_stly)}
          sub={formatPercent(s.savings_vs_stly_pct)}
          modeled
        />
        <Stat label="Award cells" value={String(detail.cells.length)} />
      </div>

      <Table className="min-w-[1100px]">
        <THead>
          <TR>
            <TH className="w-8">
              <span className="sr-only">Expand</span>
            </TH>
            <TH>Award cell · DC / Lot / Item / TF</TH>
            <TH className="text-right">Demand</TH>
            <TH className="text-right">Baseline</TH>
            <TH className="text-right">Min bid</TH>
            <TH>Recommended</TH>
          </TR>
        </THead>
        <TBody>
          {detail.cells.map((cell, i) => (
            <CellRows
              key={`${cell.dc}-${cell.lot}-${cell.item}-${cell.tf}`}
              cell={cell}
              expanded={expanded.has(i)}
              onToggle={() => toggle(i)}
            />
          ))}
        </TBody>
      </Table>
      <div className="flex items-center gap-2 border-t border-border-hairline bg-surface-subtle px-5 py-3 text-xs text-text-muted">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0" aria-hidden>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
        Engine output — decision support only. A human asserts the freeze; each
        assertion is audit-evented. DC is the locked primary grouping.
      </div>
    </Panel>
  );
}

function Stat({
  label,
  value,
  sub,
  positive,
  modeled,
}: {
  label: string;
  value: string;
  sub?: string;
  positive?: boolean;
  modeled?: boolean;
}) {
  return (
    <div className="bg-surface-card px-5 py-3">
      <div className="flex items-center gap-1.5 text-2xs font-bold uppercase tracking-wide text-text-subtle">
        {label}
        {modeled && <StatusChip tone="modeled">modeled</StatusChip>}
      </div>
      <div className="mt-0.5 font-display text-base font-bold tabular-nums text-text-strong">
        {value}
      </div>
      {sub && (
        <div
          className={cn(
            "text-xs font-semibold tabular-nums",
            positive ? "text-success" : "text-text-muted",
          )}
        >
          {sub}
        </div>
      )}
    </div>
  );
}

function CellRows({
  cell,
  expanded,
  onToggle,
}: {
  cell: ScenarioDetailCell;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <TR onClick={onToggle}>
        <TD className="text-text-subtle">{expanded ? "▾" : "▸"}</TD>
        <TD>
          <span className="font-semibold text-text-strong">{cell.dc}</span>
          <span className="text-text-subtle"> · </span>
          <span className="text-text-muted">
            {cell.lot} / {cell.item} / {cell.tf}
          </span>
        </TD>
        <TD className="text-right tabular-nums text-text">{formatCount(cell.volume)}</TD>
        <TD className="text-right tabular-nums text-text-faint">
          {formatPrice(cell.baseline_price)}
        </TD>
        <TD className="text-right tabular-nums text-text">{formatPrice(cell.min_price)}</TD>
        <TD>
          {cell.recommended ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-text-strong">
                {cell.recommended.supplier}
              </span>
              <span className="font-display tabular-nums text-text-muted">
                {formatPrice(cell.recommended.price)}
              </span>
              {cell.recommended.rec_type && (
                <StatusChip tone="neutral">{cell.recommended.rec_type}</StatusChip>
              )}
            </div>
          ) : (
            <span className="text-text-subtle">—</span>
          )}
        </TD>
      </TR>
      {expanded && (
        <TR>
          <TD colSpan={6} className="bg-surface-subtle p-0">
            <div className="px-6 py-3">
              <SupplierGrid cell={cell} />
            </div>
          </TD>
        </TR>
      )}
    </>
  );
}

function SupplierGrid({ cell }: { cell: ScenarioDetailCell }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-2xs font-bold uppercase tracking-wide text-text-subtle">
          <th className="py-1 text-left">Supplier</th>
          <th className="py-1 text-right">$/case</th>
          <th className="py-1 text-right">RecScore</th>
          <th className="py-1 text-right">Share</th>
          <th className="py-1 pl-4 text-left">Flags</th>
        </tr>
      </thead>
      <tbody>
        {cell.suppliers.length === 0 ? (
          <tr>
            <td colSpan={5} className="py-2 text-text-subtle">
              No eligible bids in this cell.
            </td>
          </tr>
        ) : (
          cell.suppliers.map((sup) => (
            <tr key={sup.name} className="border-t border-border-hairline">
              <td className="py-1.5 text-text-strong">{sup.name}</td>
              <td className="py-1.5 text-right font-display tabular-nums text-text">
                {formatPrice(sup.price_per_case)}
              </td>
              <td className="py-1.5 text-right tabular-nums text-text-muted">
                {sup.rec_score == null ? "—" : sup.rec_score.toFixed(1)}
              </td>
              <td className="py-1.5 text-right tabular-nums text-text">
                {sup.volume_share > 0 ? formatPercent(sup.volume_share) : "—"}
              </td>
              <td className="py-1.5 pl-4">
                <div className="flex flex-wrap gap-1">
                  {sup.is_recommended && <StatusChip tone="green">Awarded</StatusChip>}
                  {sup.is_min && <StatusChip tone="accent">Min</StatusChip>}
                  {sup.is_incumbent && <StatusChip tone="slate">Incumbent</StatusChip>}
                </div>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
