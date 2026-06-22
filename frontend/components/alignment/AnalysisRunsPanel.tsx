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
import { formatTimestamp } from "@/lib/format";
import type { AnalysisSummary } from "@/lib/api";
import { RunAnalysisControl } from "./RunAnalysisControl";

// The sealed analyses for this cycle + the control to seal a new one. Each row is a
// versioned, immutable engine seal for a round; the latest is live and the prior ones
// open read-only. Selecting one drives the scenario comparison below.
export function AnalysisRunsPanel({
  analyses,
  selectedId,
  onSelect,
  onRun,
  onSaveVersion,
  running,
}: {
  analyses: AnalysisSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRun: (round: number) => void;
  // Open the lightweight "save this version" (savepoint) flow for a sealed run.
  onSaveVersion: (a: AnalysisSummary) => void;
  running: boolean;
}) {
  // The live version is the most recently sealed (highest version); earlier seals are
  // immutable, read-only history.
  const liveId = analyses.length
    ? analyses.reduce((a, b) => (b.version > a.version ? b : a)).analysis_run_id
    : null;

  return (
    <Panel>
      <PanelHeader
        title={
          <span className="font-display text-base font-bold text-text-strong">
            Sealed analyses
          </span>
        }
        description="Each seal is an immutable engine output (scores + seven scenarios) for a round. The latest is live; prior versions open read-only."
        actions={<RunAnalysisControl onRun={onRun} running={running} />}
      />
      {analyses.length === 0 ? (
        <div className="px-5 py-10 text-center text-sm text-text-muted">
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
              <TH>
                <span className="sr-only">Actions</span>
              </TH>
            </TR>
          </THead>
          <TBody>
            {analyses.map((a) => {
              const selected = a.analysis_run_id === selectedId;
              const live = a.analysis_run_id === liveId;
              return (
                <TR
                  key={a.analysis_run_id}
                  onClick={() => onSelect(a.analysis_run_id)}
                  className={selected ? "bg-accent-soft" : undefined}
                >
                  <TD className="font-semibold text-text-strong">
                    <span className="inline-flex flex-wrap items-center gap-2">
                      v{a.version}
                      <StatusChip tone={live ? "green" : "sealed"}>
                        {live ? "Live" : "Read-only"}
                      </StatusChip>
                      {a.label && <StatusChip tone="accent">{a.label}</StatusChip>}
                      {selected && !a.label && (
                        <StatusChip tone="accent">Selected</StatusChip>
                      )}
                    </span>
                  </TD>
                  <TD className="text-text">Round {a.round_number}</TD>
                  <TD className="text-text-muted">{a.engine_version}</TD>
                  <TD className="text-text-muted">{formatTimestamp(a.sealed_at)}</TD>
                  <TD className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSaveVersion(a);
                      }}
                    >
                      {a.label ? "Rename" : "Save version"}
                    </Button>
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
