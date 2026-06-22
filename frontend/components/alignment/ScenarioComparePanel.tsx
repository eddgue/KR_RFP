"use client";

import { useEffect, useState } from "react";
import { ApiError, getScenarioComparison } from "@/lib/api";
import type { AnalysisSummary, ScenarioComparisonRow } from "@/lib/api";
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
import { formatMoney, formatPercent } from "@/lib/format";

function title(a: AnalysisSummary): string {
  return a.label ? `v${a.version} · ${a.label}` : `v${a.version}`;
}

// Compare the LIVE working build (left) against a SAVED version (right): the same seven lenses,
// matched by lens code, with the saved-minus-working spend Δ. Reuses the sealed scenario reads —
// the numbers are identical to each version's own comparison (no re-derivation).
export function ScenarioComparePanel({
  slug,
  left,
  right,
}: {
  slug: string;
  left: AnalysisSummary;
  right: AnalysisSummary;
}) {
  const [rows, setRows] = useState<{
    left: ScenarioComparisonRow[];
    right: ScenarioComparisonRow[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setRows(null);
    setError(null);
    Promise.all([
      getScenarioComparison(slug, left.analysis_run_id),
      getScenarioComparison(slug, right.analysis_run_id),
    ])
      .then(([l, r]) => {
        if (active) setRows({ left: l, right: r });
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.detail : "Could not load the comparison.");
        }
      });
    return () => {
      active = false;
    };
  }, [slug, left.analysis_run_id, right.analysis_run_id]);

  const merged = rows
    ? rows.left.map((l) => ({
        code: l.code,
        label: l.label,
        l,
        r: rows.right.find((x) => x.code === l.code) ?? null,
      }))
    : [];

  return (
    <Panel>
      <PanelHeader
        title={
          <span className="font-display text-base font-bold text-text-strong">
            Compare versions
          </span>
        }
        description="The seven lenses for two versions side by side — your live working build vs a saved version. Δ is the saved version minus the working build (red = costs more)."
      />
      {error ? (
        <div className="px-5 py-8 text-center text-sm text-danger">{error}</div>
      ) : !rows ? (
        <div className="px-5 py-8 text-center text-sm text-text-muted">Loading comparison…</div>
      ) : (
        <Table className="min-w-[820px]">
          <THead>
            <TR>
              <TH>Lens</TH>
              <TH className="text-right">{title(left)} · working</TH>
              <TH className="text-right">{title(right)} · saved</TH>
              <TH className="text-right">Δ spend</TH>
              <TH className="text-right">Save vs incumbent (work · saved)</TH>
            </TR>
          </THead>
          <TBody>
            {merged.map(({ code, label, l, r }) => {
              const delta = r ? r.total_spend - l.total_spend : null;
              return (
                <TR key={code}>
                  <TD>
                    <span className="font-semibold text-text-strong">{code}</span>{" "}
                    <span className="text-text-muted">{label}</span>
                    {l.is_recommended && (
                      <StatusChip tone="green" className="ml-1.5">
                        REC
                      </StatusChip>
                    )}
                  </TD>
                  <TD className="text-right font-display font-semibold tabular-nums text-text-strong">
                    {formatMoney(l.total_spend)}
                  </TD>
                  <TD className="text-right tabular-nums text-text">
                    {r ? formatMoney(r.total_spend) : "—"}
                  </TD>
                  <TD
                    className={cn(
                      "text-right font-semibold tabular-nums",
                      delta == null || delta === 0
                        ? "text-text-faint"
                        : delta > 0
                          ? "text-danger"
                          : "text-success",
                    )}
                  >
                    {delta == null || delta === 0
                      ? "—"
                      : `${delta > 0 ? "+" : ""}${formatMoney(delta)}`}
                  </TD>
                  <TD className="text-right tabular-nums text-text-muted">
                    {formatPercent(l.savings_vs_incumbent_pct)}
                    {" · "}
                    {r ? formatPercent(r.savings_vs_incumbent_pct) : "—"}
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
