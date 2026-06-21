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

// One lens inspected cell-by-cell: the savings headline, the governed freeze
// action, and the per-(DC × lot × item × TF) competitive grid. Each cell row
// expands to the full supplier picture (price, RecScore, awarded share, flags).
export function ScenarioDetailPanel({
  detail,
  frozenAwardId,
  onFreeze,
}: {
  detail: ScenarioDetail;
  frozenAwardId: string | null;
  onFreeze: () => void;
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

  return (
    <Panel>
      <PanelHeader
        title={
          <span className="flex items-center gap-2">
            <span>
              Lens {detail.code} — {detail.label}
            </span>
            {detail.is_recommended && <StatusChip tone="green">Recommended</StatusChip>}
          </span>
        }
        description={detail.description}
        actions={
          frozenAwardId ? (
            <StatusChip tone="green">Frozen · {frozenAwardId.slice(0, 8)}</StatusChip>
          ) : (
            <Button size="sm" onClick={onFreeze}>
              Freeze this lens
            </Button>
          )
        }
      />

      <div className="grid grid-cols-2 gap-px bg-line sm:grid-cols-4">
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
          positive
        />
        <Stat label="Cells" value={String(detail.cells.length)} />
      </div>

      <Table>
        <THead>
          <TR>
            <TH className="w-8">
              <span className="sr-only">Expand</span>
            </TH>
            <TH>Cell · DC / Lot / Item / TF</TH>
            <TH className="text-right">Volume</TH>
            <TH className="text-right">Baseline</TH>
            <TH className="text-right">Min bid</TH>
            <TH>Awarded</TH>
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
    </Panel>
  );
}

function Stat({
  label,
  value,
  sub,
  positive,
}: {
  label: string;
  value: string;
  sub?: string;
  positive?: boolean;
}) {
  return (
    <div className="bg-surface px-5 py-3">
      <div className="text-2xs uppercase tracking-wide text-ink-subtle">{label}</div>
      <div className="mt-0.5 text-base font-semibold tabular-nums text-ink">{value}</div>
      {sub && (
        <div
          className={cn(
            "text-xs tabular-nums",
            positive ? "text-emerald-700" : "text-ink-muted",
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
        <TD className="text-ink-subtle">{expanded ? "▾" : "▸"}</TD>
        <TD>
          <span className="font-medium text-ink">{cell.dc}</span>
          <span className="text-ink-subtle"> · </span>
          <span className="text-ink-muted">
            {cell.lot} / {cell.item} / {cell.tf}
          </span>
        </TD>
        <TD className="text-right tabular-nums">{formatCount(cell.volume)}</TD>
        <TD className="text-right tabular-nums text-ink-muted">
          {formatPrice(cell.baseline_price)}
        </TD>
        <TD className="text-right tabular-nums">{formatPrice(cell.min_price)}</TD>
        <TD>
          {cell.recommended ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-ink">{cell.recommended.supplier}</span>
              <span className="tabular-nums text-ink-muted">
                {formatPrice(cell.recommended.price)}
              </span>
              {cell.recommended.rec_type && (
                <StatusChip tone="neutral">{cell.recommended.rec_type}</StatusChip>
              )}
            </div>
          ) : (
            <span className="text-ink-subtle">—</span>
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
        <tr className="text-2xs uppercase tracking-wide text-ink-subtle">
          <th className="py-1 text-left font-semibold">Supplier</th>
          <th className="py-1 text-right font-semibold">$/case</th>
          <th className="py-1 text-right font-semibold">RecScore</th>
          <th className="py-1 text-right font-semibold">Share</th>
          <th className="py-1 pl-4 text-left font-semibold">Flags</th>
        </tr>
      </thead>
      <tbody>
        {cell.suppliers.length === 0 ? (
          <tr>
            <td colSpan={5} className="py-2 text-ink-subtle">
              No eligible bids in this cell.
            </td>
          </tr>
        ) : (
          cell.suppliers.map((sup) => (
            <tr key={sup.name} className="border-t border-line">
              <td className="py-1.5 text-ink">{sup.name}</td>
              <td className="py-1.5 text-right tabular-nums">
                {formatPrice(sup.price_per_case)}
              </td>
              <td className="py-1.5 text-right tabular-nums text-ink-muted">
                {sup.rec_score == null ? "—" : sup.rec_score.toFixed(1)}
              </td>
              <td className="py-1.5 text-right tabular-nums">
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
