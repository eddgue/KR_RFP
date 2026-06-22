"use client";

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
import { formatPercent, formatPrice, formatTimestamp } from "@/lib/format";
import type { AwardDetail } from "@/lib/api";

// One frozen award, in the two-column post-award layout. LEFT: the award card — the
// awarded lines (frozen baseline → current effective price, per DC × Lot × TF) plus
// the close-out / post-award layer summary. RIGHT: the chronological audit trail
// (v0 FROZEN → vN append-only layers). A positive Δ means the effective price rose
// above the frozen baseline. The governed actions (Record adjustment, Finalize &
// close run) surface in the header; their POSTs are owned by the page.
export function AwardDetailPanel({
  detail,
  onAdjust,
  onFinalize,
  canFinalize = false,
}: {
  detail: AwardDetail;
  onAdjust?: () => void;
  onFinalize?: () => void;
  /** Enabled only when there is a FROZEN award to close out against. */
  canFinalize?: boolean;
}) {
  // §B5 — rollups reflect the lines actually shown, never a stale full count.
  const adjustedLines = detail.lines.filter((l) => l.delta !== 0).length;

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1.6fr)_minmax(280px,1fr)] lg:items-start">
      {/* LEFT: award card + close-out */}
      <div className="flex flex-col gap-5">
        <Panel>
          <PanelHeader
            title={
              <span className="flex flex-wrap items-center gap-2">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-control bg-success-bg text-success">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" aria-hidden>
                    <rect x="5" y="11" width="14" height="9" rx="2" />
                    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
                  </svg>
                </span>
                <span className="font-display text-base font-bold text-text-strong">
                  {detail.award_code}
                </span>
                <StatusChip tone="frozen">Frozen · Lens {detail.scenario_code}</StatusChip>
                {detail.latest_version > 0 && (
                  <StatusChip tone="amber">v{detail.latest_version}</StatusChip>
                )}
              </span>
            }
            description={
              <>
                Frozen {formatTimestamp(detail.frozen_at)} by{" "}
                <b className="text-text">{detail.frozen_by}</b> · immutable baseline ·{" "}
                {detail.lines.length} {detail.lines.length === 1 ? "cell" : "cells"}
                {adjustedLines > 0 && (
                  <> · {adjustedLines} repriced</>
                )}
              </>
            }
            actions={
              <div className="flex flex-wrap items-center gap-2">
                {onAdjust && (
                  <Button variant="secondary" size="sm" onClick={onAdjust}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden>
                      <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
                    </svg>
                    Record adjustment
                  </Button>
                )}
                {onFinalize && (
                  <Button
                    size="sm"
                    onClick={onFinalize}
                    disabled={!canFinalize}
                    title={
                      canFinalize
                        ? undefined
                        : "A FROZEN award is required to close out the run."
                    }
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden>
                      <rect x="5" y="11" width="14" height="9" rx="2" />
                      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
                    </svg>
                    Finalize &amp; close run
                  </Button>
                )}
              </div>
            }
          />
          <Table className="min-w-[760px]">
            <THead>
              <TR>
                <TH>Award cell</TH>
                <TH>Supplier</TH>
                <TH className="text-right">Share</TH>
                <TH className="text-right">Frozen $/case</TH>
                <TH className="text-right">Effective $/case</TH>
                <TH className="text-right">Δ</TH>
              </TR>
            </THead>
            <TBody>
              {detail.lines.map((l) => (
                <TR key={`${l.dc}-${l.lot}-${l.tf}-${l.supplier}`}>
                  <TD>
                    <div className="font-semibold text-text-strong">{l.dc}</div>
                    <div className="text-2xs text-text-subtle">
                      {l.lot} · {l.tf}
                    </div>
                  </TD>
                  <TD className="font-medium text-text">{l.supplier}</TD>
                  <TD className="text-right tabular-nums text-text">
                    {formatPercent(l.volume_share)}
                  </TD>
                  <TD className="text-right tabular-nums text-text-faint">
                    {formatPrice(l.frozen_price)}
                  </TD>
                  <TD className="text-right font-display font-semibold tabular-nums text-text-strong">
                    {formatPrice(l.effective_price)}
                  </TD>
                  <TD
                    className={cn(
                      "text-right font-semibold tabular-nums",
                      l.delta > 0
                        ? "text-danger"
                        : l.delta < 0
                          ? "text-success"
                          : "text-text-subtle",
                    )}
                  >
                    {l.delta === 0
                      ? "—"
                      : `${l.delta > 0 ? "+" : "−"}${formatPrice(Math.abs(l.delta))}`}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <div className="flex items-start gap-2 border-t border-border-hairline bg-surface-subtle px-5 py-3 text-xs text-text-muted">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-px shrink-0" aria-hidden>
              <circle cx="12" cy="12" r="9" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            <span>
              The <b>frozen</b> column is the immutable baseline (v0). The{" "}
              <b>effective</b> column reflects all append-only post-award layers to
              date. The award record is authoritative — generated guides are renders
              of it.
            </span>
          </div>
        </Panel>
      </div>

      {/* RIGHT: chronological audit trail */}
      <Panel>
        <PanelHeader
          title={
            <span className="font-display text-base font-bold text-text-strong">
              Audit trail
            </span>
          }
          description="v0 is the frozen baseline; each later version is an append-only, date-stamped layer."
        />
        <Table>
          <THead>
            <TR>
              <TH>Version</TH>
              <TH>Type</TH>
              <TH>Effective</TH>
              <TH>Reason</TH>
              <TH className="text-right">Cells</TH>
              <TH>Recorded</TH>
            </TR>
          </THead>
          <TBody>
            {detail.versions.map((v) => (
              <TR key={v.version_no}>
                <TD>
                  {v.version_no === 0 ? (
                    <StatusChip tone="frozen">v0 · FROZEN</StatusChip>
                  ) : (
                    <StatusChip tone="amber">v{v.version_no}</StatusChip>
                  )}
                </TD>
                <TD className="text-text">{v.adjustment_type}</TD>
                <TD className="tabular-nums text-text-muted">{v.effective_date}</TD>
                <TD className="text-text-muted">{v.reason}</TD>
                <TD className="text-right tabular-nums text-text">{v.n_lines}</TD>
                <TD className="text-text-muted">
                  {v.created_by} · {formatTimestamp(v.created_at)}
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Panel>
    </div>
  );
}
