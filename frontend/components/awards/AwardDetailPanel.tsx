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

// One frozen award: the awarded lines (frozen baseline → current effective price,
// per cell) and the full version history (v0 FROZEN → vN append-only layers). A
// positive Δ means the effective price rose above the frozen baseline. `onAdjust`,
// when provided, surfaces the "Record adjustment" action in the header.
export function AwardDetailPanel({
  detail,
  onAdjust,
}: {
  detail: AwardDetail;
  onAdjust?: () => void;
}) {
  return (
    <>
      <Panel>
        <PanelHeader
          title={
            <span className="flex flex-wrap items-center gap-2">
              <span>{detail.award_code}</span>
              <StatusChip tone="green">Frozen · Lens {detail.scenario_code}</StatusChip>
              {detail.latest_version > 0 && (
                <StatusChip tone="amber">v{detail.latest_version}</StatusChip>
              )}
            </span>
          }
          description={`Frozen ${formatTimestamp(detail.frozen_at)} by ${detail.frozen_by} · ${detail.lines.length} cells`}
          actions={
            onAdjust && (
              <Button variant="secondary" size="sm" onClick={onAdjust}>
                Record adjustment
              </Button>
            )
          }
        />
        <Table>
          <THead>
            <TR>
              <TH>DC</TH>
              <TH>Lot</TH>
              <TH>TF</TH>
              <TH>Supplier</TH>
              <TH className="text-right">Share</TH>
              <TH className="text-right">Frozen</TH>
              <TH className="text-right">Effective</TH>
              <TH className="text-right">Δ</TH>
            </TR>
          </THead>
          <TBody>
            {detail.lines.map((l) => (
              <TR key={`${l.dc}-${l.lot}-${l.tf}-${l.supplier}`}>
                <TD className="text-ink">{l.dc}</TD>
                <TD className="text-ink-muted">{l.lot}</TD>
                <TD className="text-ink-muted">{l.tf}</TD>
                <TD className="font-medium text-ink">{l.supplier}</TD>
                <TD className="text-right tabular-nums">{formatPercent(l.volume_share)}</TD>
                <TD className="text-right tabular-nums text-ink-muted">
                  {formatPrice(l.frozen_price)}
                </TD>
                <TD className="text-right tabular-nums">{formatPrice(l.effective_price)}</TD>
                <TD
                  className={cn(
                    "text-right tabular-nums",
                    l.delta > 0
                      ? "text-red-700"
                      : l.delta < 0
                        ? "text-emerald-700"
                        : "text-ink-subtle",
                  )}
                >
                  {l.delta === 0 ? "—" : `${l.delta > 0 ? "+" : "−"}${formatPrice(Math.abs(l.delta))}`}
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Panel>

      <Panel>
        <PanelHeader
          title="Version history"
          description="v0 is the frozen baseline; each later version is an append-only, date-stamped price layer."
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
                    <StatusChip tone="green">v0 · FROZEN</StatusChip>
                  ) : (
                    <StatusChip tone="amber">v{v.version_no}</StatusChip>
                  )}
                </TD>
                <TD className="text-ink">{v.adjustment_type}</TD>
                <TD className="tabular-nums text-ink-muted">{v.effective_date}</TD>
                <TD className="text-ink-muted">{v.reason}</TD>
                <TD className="text-right tabular-nums">{v.n_lines}</TD>
                <TD className="text-ink-muted">
                  {v.created_by} · {formatTimestamp(v.created_at)}
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Panel>
    </>
  );
}
