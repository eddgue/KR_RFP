import type { MappingConfidence, MappingProposalView } from "@/lib/api";
import {
  StatusChip,
  Table,
  THead,
  TBody,
  TR,
  TH,
  TD,
} from "@/components/ui";
import { Alert } from "./Alert";

function confidenceTone(c: MappingConfidence) {
  if (c === "high") return "green" as const;
  if (c === "medium") return "amber" as const;
  return "slate" as const;
}

// Read-only view of a flexible-import dry run: which sheet/header row, the
// inferred field → column mappings, any ambiguities, and the summary. Makes it
// explicit that nothing has been written yet.
export function MappingProposal({
  proposal,
}: {
  proposal: MappingProposalView;
}) {
  const entries = Object.entries(proposal.mappings);

  return (
    <div className="flex flex-col gap-4">
      <Alert tone="warning">
        Nothing has been imported yet. Review the proposed mapping below, then
        choose <span className="font-medium">Confirm &amp; import</span> to write
        the bids.
      </Alert>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <p className="text-2xs uppercase tracking-wide text-text-subtle">Sheet</p>
          <p className="mt-0.5 text-sm font-semibold text-text-strong">
            {proposal.sheet_name}
          </p>
        </div>
        <div>
          <p className="text-2xs uppercase tracking-wide text-text-subtle">
            Header row
          </p>
          <p className="mt-0.5 text-sm font-semibold tabular-nums text-text-strong">
            {proposal.header_row}
          </p>
        </div>
        <div>
          <p className="text-2xs uppercase tracking-wide text-text-subtle">
            Mappings
          </p>
          <p className="mt-0.5 text-sm font-semibold tabular-nums text-text-strong">
            {entries.length}
          </p>
        </div>
        <div>
          <p className="text-2xs uppercase tracking-wide text-text-subtle">
            Confidence
          </p>
          <p className="mt-0.5">
            <StatusChip tone={proposal.is_confident ? "green" : "amber"}>
              {proposal.is_confident ? "Confident" : "Needs review"}
            </StatusChip>
          </p>
        </div>
      </div>

      {proposal.summary && (
        <Alert tone="info">{proposal.summary}</Alert>
      )}

      <div className="overflow-hidden rounded-card border border-border">
        <Table>
          <THead>
            <TR>
              <TH>Field</TH>
              <TH>Source header</TH>
              <TH className="text-right">Column</TH>
              <TH>Basis</TH>
              <TH>Confidence</TH>
            </TR>
          </THead>
          <TBody>
            {entries.length === 0 ? (
              <TR>
                <TD className="text-text-subtle" colSpan={5}>
                  No fields were mapped.
                </TD>
              </TR>
            ) : (
              entries.map(([key, m]) => (
                <TR key={key}>
                  <TD className="font-semibold">{m.field}</TD>
                  <TD className="text-text-muted">{m.source_header}</TD>
                  <TD className="text-right tabular-nums text-text-muted">
                    {m.column_index}
                  </TD>
                  <TD className="text-text-muted">{m.basis}</TD>
                  <TD>
                    <StatusChip tone={confidenceTone(m.confidence)}>
                      {m.confidence}
                    </StatusChip>
                  </TD>
                </TR>
              ))
            )}
          </TBody>
        </Table>
      </div>

      {proposal.ambiguities.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <p className="text-sm font-semibold text-text-strong">Ambiguities</p>
          <ul className="flex flex-col gap-1 rounded-card border border-warning/30 bg-warning-bg px-4 py-3 text-sm text-warning">
            {proposal.ambiguities.map((a, i) => (
              <li key={i} className="list-inside list-disc">
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
