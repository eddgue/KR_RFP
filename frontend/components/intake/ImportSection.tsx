"use client";

import { useState } from "react";
import { ApiError, importBids, isBidImportProposal } from "@/lib/api";
import type {
  BidImportMode,
  KanbanResponse,
  MappingProposalView,
} from "@/lib/api";
import { Button, FileInput, Panel, PanelHeader } from "@/components/ui";
import { cn } from "@/lib/cn";
import { Alert } from "./Alert";
import { MappingProposal } from "./MappingProposal";

export interface ImportSectionProps {
  slug: string;
  round: number;
  disabled: boolean;
  onImported: (ingested: number, kanban: KanbanResponse) => void;
}

const MODES: { value: BidImportMode; title: string; hint: string }[] = [
  {
    value: "strict",
    title: "Our template (strict)",
    hint: "The supplier filled in the generated template — import directly.",
  },
  {
    value: "flexible",
    title: "Supplier's own file (flexible)",
    hint: "A non-template file — propose a column mapping for you to review first.",
  },
];

// Step 3 — import bids. Strict mode writes directly and reports the count.
// Flexible mode first proposes a mapping (nothing written), which the user then
// confirms to import.
export function ImportSection({
  slug,
  round,
  disabled,
  onImported,
}: ImportSectionProps) {
  const [mode, setMode] = useState<BidImportMode>("strict");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gate, setGate] = useState<string | null>(null);
  const [ingested, setIngested] = useState<number | null>(null);
  const [proposal, setProposal] = useState<MappingProposalView | null>(null);

  function resetResults() {
    setError(null);
    setGate(null);
    setIngested(null);
    setProposal(null);
  }

  function handleError(err: unknown, fallback: string) {
    if (err instanceof ApiError && err.isGateRequired) {
      setGate(err.detail || "Complete the earlier steps before importing bids.");
    } else {
      setError(err instanceof ApiError ? err.detail || fallback : fallback);
    }
  }

  // Initial submit: strict imports directly; flexible requests a proposal.
  async function onSubmit() {
    if (!file) return;
    resetResults();
    setSubmitting(true);
    try {
      const res = await importBids({
        run: slug,
        round,
        mode,
        confirm: false,
        file,
      });
      if (isBidImportProposal(res)) {
        setProposal(res.proposal);
      } else {
        setIngested(res.ingested);
        setFile(null);
        onImported(res.ingested, res.kanban);
      }
    } catch (err) {
      handleError(err, "Could not import the bid file.");
    } finally {
      setSubmitting(false);
    }
  }

  // Confirm a flexible proposal: re-submit the same file with confirm=true.
  async function onConfirm() {
    if (!file) return;
    setError(null);
    setGate(null);
    setConfirming(true);
    try {
      const res = await importBids({
        run: slug,
        round,
        mode: "flexible",
        confirm: true,
        file,
      });
      if (!isBidImportProposal(res)) {
        setIngested(res.ingested);
        setProposal(null);
        setFile(null);
        onImported(res.ingested, res.kanban);
      }
    } catch (err) {
      handleError(err, "Could not confirm the import.");
    } finally {
      setConfirming(false);
    }
  }

  function cancelProposal() {
    setProposal(null);
  }

  const busy = submitting || confirming;

  return (
    <Panel>
      <PanelHeader
        title="3 · Import bids"
        description={`Upload supplier bids for round ${round}.`}
      />
      <div className="flex flex-col gap-4 px-5 py-5">
        {disabled && (
          <Alert tone="info">
            Generate this round&apos;s template before importing bids.
          </Alert>
        )}

        <fieldset className="flex flex-col gap-2" disabled={disabled || busy}>
          <legend className="mb-1 text-sm font-medium text-ink">
            Source format
          </legend>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {MODES.map((m) => {
              const active = mode === m.value;
              return (
                <label
                  key={m.value}
                  className={cn(
                    "flex cursor-pointer items-start gap-2.5 rounded-md border px-3 py-2.5 transition-colors",
                    active
                      ? "border-accent bg-accent-soft"
                      : "border-line bg-surface-subtle hover:bg-surface-muted",
                    (disabled || busy) && "cursor-not-allowed opacity-70",
                  )}
                >
                  <input
                    type="radio"
                    name="import-mode"
                    className="mt-0.5 h-4 w-4 border-line-strong text-accent focus:ring-2 focus:ring-accent/40"
                    checked={active}
                    onChange={() => {
                      setMode(m.value);
                      resetResults();
                    }}
                    disabled={disabled || busy}
                  />
                  <span className="text-sm">
                    <span className="font-medium text-ink">{m.title}</span>
                    <span className="block text-xs text-ink-muted">{m.hint}</span>
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <FileInput
            file={file}
            onChange={(f) => {
              setFile(f);
              // A new file invalidates any prior proposal/result.
              setProposal(null);
              setIngested(null);
            }}
            accept=".xlsx"
            disabled={disabled || busy}
            className="sm:flex-1"
            buttonLabel="Choose .xlsx"
          />
          <Button
            onClick={() => void onSubmit()}
            loading={submitting}
            disabled={disabled || !file || confirming}
          >
            {mode === "flexible" ? "Propose mapping" : "Import bids"}
          </Button>
        </div>

        {gate && <Alert tone="warning">{gate}</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
        {ingested != null && !error && (
          <Alert tone="success">
            Imported{" "}
            <span className="font-semibold tabular-nums">{ingested}</span> bid
            line{ingested === 1 ? "" : "s"}.
          </Alert>
        )}

        {proposal && (
          <div className="flex flex-col gap-4 rounded-md border border-line bg-surface-subtle p-4">
            <MappingProposal proposal={proposal} />
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="secondary"
                onClick={cancelProposal}
                disabled={confirming}
              >
                Cancel
              </Button>
              <Button onClick={() => void onConfirm()} loading={confirming}>
                Confirm &amp; import
              </Button>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
