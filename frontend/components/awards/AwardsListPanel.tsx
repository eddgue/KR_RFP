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
        title="Frozen awards"
        description="Each award is an immutable baseline; post-award price moves are append-only, versioned layers."
      />
      {awards.length === 0 ? (
        <div className="px-5 py-10 text-center text-sm text-ink-muted">
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
                  <TD className="font-medium text-ink">
                    {a.award_code}
                    {selected && (
                      <StatusChip tone="accent" className="ml-2">
                        Selected
                      </StatusChip>
                    )}
                  </TD>
                  <TD>Lens {a.scenario_code}</TD>
                  <TD className="text-right tabular-nums">{a.line_count}</TD>
                  <TD>
                    {a.latest_version === 0 ? (
                      <span className="text-ink-muted">baseline</span>
                    ) : (
                      <StatusChip tone="amber">v{a.latest_version}</StatusChip>
                    )}
                  </TD>
                  <TD className="text-ink-muted">{formatTimestamp(a.frozen_at)}</TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
    </Panel>
  );
}
