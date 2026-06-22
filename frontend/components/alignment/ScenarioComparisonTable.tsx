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
import { formatCount, formatMoney, formatPercent } from "@/lib/format";
import type { ScenarioComparisonRow } from "@/lib/api";

// The seven lenses side by side — the "which scenario" decision surface. Numbers
// are identical to the alignment workbook's Scenario Comparison tab (same gather).
// B is flagged Recommended; A is the lowest-cost benchmark Δ is measured against.
export function ScenarioComparisonTable({
  rows,
  selectedCode,
  onSelect,
}: {
  rows: ScenarioComparisonRow[];
  selectedCode: string | null;
  onSelect: (code: string) => void;
}) {
  return (
    <Panel>
      <PanelHeader
        title="Scenario comparison"
        description="The seven lenses A–G. Lens B is the recommended default; A is the lowest-cost benchmark. Select a lens to inspect it cell by cell."
      />
      <Table>
        <THead>
          <TR>
            <TH>Lens</TH>
            <TH className="text-right">Spend</TH>
            <TH className="text-right">Δ vs A</TH>
            <TH className="text-right">Save vs incumbent</TH>
            <TH className="text-right">Save vs STLY</TH>
            <TH className="text-right">Suppliers</TH>
            <TH className="text-right">Cells</TH>
            <TH className="text-right">Over capacity</TH>
          </TR>
        </THead>
        <TBody>
          {rows.map((r) => {
            const selected = r.code === selectedCode;
            return (
              <TR
                key={r.code}
                onClick={() => onSelect(r.code)}
                className={selected ? "bg-accent-soft" : undefined}
              >
                <TD>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-ink">{r.code}</span>
                    <span className="text-ink-muted">{r.label}</span>
                    {r.is_recommended && (
                      <StatusChip tone="green">Recommended</StatusChip>
                    )}
                  </div>
                </TD>
                <TD className="text-right tabular-nums">
                  {formatMoney(r.total_spend)}
                </TD>
                <TD className="text-right tabular-nums text-ink-muted">
                  {r.delta_vs_a === 0 ? "—" : formatMoney(r.delta_vs_a)}
                </TD>
                <TD className="text-right tabular-nums text-emerald-700">
                  {formatPercent(r.savings_vs_incumbent_pct)}
                </TD>
                <TD className="text-right tabular-nums text-emerald-700">
                  {formatPercent(r.savings_vs_stly_pct)}
                </TD>
                <TD className="text-right tabular-nums">
                  {formatCount(r.supplier_count)}
                </TD>
                <TD className="text-right tabular-nums">
                  {formatCount(r.cell_count)}
                </TD>
                <TD className="text-right tabular-nums">
                  {r.cap_breach_count > 0 ? (
                    <span className="text-amber-700">{r.cap_breach_count}</span>
                  ) : (
                    "—"
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
