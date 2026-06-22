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
import { formatTimestamp } from "@/lib/format";
import type { AwardSummary } from "@/lib/api";

// The cycle's frozen awards. Each is an immutable baseline; post-award price moves
// are append-only versioned layers (the latest version is shown). Selecting one
// drives the detail panel below.
export function AwardsListPanel({
  awards,
  selectedId,
  onSelect,
}: {
  awards: AwardSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <Panel>
      <PanelHeader
        title={
          <span className="font-display text-base font-bold text-text-strong">
            Frozen awards
          </span>
        }
        description="Each award is an immutable baseline; post-award price moves are append-only, versioned layers."
      />
      {awards.length === 0 ? (
        <div className="px-5 py-10 text-center text-sm text-text-muted">
          No frozen award yet — freeze a scenario on the alignment screen to create
          one.
        </div>
      ) : (
        <Table>
          <THead>
            <TR>
              <TH>Award</TH>
              <TH>Scenario</TH>
              <TH className="text-right">Cells</TH>
              <TH>Version</TH>
              <TH>Frozen</TH>
            </TR>
          </THead>
          <TBody>
            {awards.map((a) => {
              const selected = a.award_id === selectedId;
              return (
                <TR
                  key={a.award_id}
                  onClick={() => onSelect(a.award_id)}
                  className={selected ? "bg-accent-soft" : undefined}
                >
                  <TD className="font-semibold text-text-strong">
                    <span className="inline-flex items-center gap-2">
                      {a.award_code}
                      <StatusChip tone="frozen">Frozen</StatusChip>
                      {selected && <StatusChip tone="accent">Selected</StatusChip>}
                    </span>
                  </TD>
                  <TD className="text-text">Lens {a.scenario_code}</TD>
                  <TD className="text-right tabular-nums text-text">{a.line_count}</TD>
                  <TD>
                    {a.latest_version === 0 ? (
                      <span className="text-text-muted">baseline</span>
                    ) : (
                      <StatusChip tone="amber">v{a.latest_version}</StatusChip>
                    )}
                  </TD>
                  <TD className="text-text-muted">{formatTimestamp(a.frozen_at)}</TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
    </Panel>
  );
}
