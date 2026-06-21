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
import type { AnalysisSummary } from "@/lib/api";
import { RunAnalysisControl } from "./RunAnalysisControl";

// The sealed analysis runs for this cycle + the control to seal a new one. Each
// run is a versioned, immutable engine seal for a round; selecting one drives the
// scenario comparison below.
export function AnalysisRunsPanel({
  analyses,
  selectedId,
  onSelect,
  onRun,
  running,
}: {
  analyses: AnalysisSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRun: (round: number) => void;
  running: boolean;
}) {
  return (
    <Panel>
      <PanelHeader
        title="Analysis runs"
        description="Each run seals the engine output (scores + seven scenarios) for a round. Pick one to compare its scenarios."
        actions={<RunAnalysisControl onRun={onRun} running={running} />}
      />
      {analyses.length === 0 ? (
        <div className="px-5 py-10 text-center text-sm text-ink-muted">
          No sealed analysis yet — run a round to score the bids and generate the
          seven scenarios.
        </div>
      ) : (
        <Table>
          <THead>
            <TR>
              <TH>Version</TH>
              <TH>Round</TH>
              <TH>Engine</TH>
              <TH>Sealed</TH>
            </TR>
          </THead>
          <TBody>
            {analyses.map((a) => {
              const selected = a.analysis_run_id === selectedId;
              return (
                <TR
                  key={a.analysis_run_id}
                  onClick={() => onSelect(a.analysis_run_id)}
                  className={selected ? "bg-accent-soft" : undefined}
                >
                  <TD className="font-medium text-ink">
                    v{a.version}
                    {selected && (
                      <StatusChip tone="accent" className="ml-2">
                        Selected
                      </StatusChip>
                    )}
                  </TD>
                  <TD>Round {a.round_number}</TD>
                  <TD className="text-ink-muted">{a.engine_version}</TD>
                  <TD className="text-ink-muted">{formatTimestamp(a.sealed_at)}</TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
    </Panel>
  );
}
