"use client";

import { useState } from "react";
import { ApiError, importBids, isBidImportProposal } from "@/lib/api";
import type {
  BidImportMode,
  KanbanResponse,
  MappingProposalView,
} from "@/lib/api";
import { Button, FileInput, Panel, StatusChip } from "@/components/ui";
import { cn } from "@/lib/cn";
import { Alert } from "./Alert";
import { MappingProposal } from "./MappingProposal";
import { StepHeader } from "./StepHeader";

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
  const imported = ingested != null && !error;
  const stepState = disabled ? "todo" : imported ? "done" : "current";

  return (
    <Panel>
      <StepHeader
        step={3}
        title="Load supplier bids"
        description="Upload returned bid workbooks. Keys are validated and unrecognized rows are quarantined — never guessed."
        state={stepState}
        actions={
          imported ? (
            <StatusChip tone="green">Complete</StatusChip>
          ) : disabled ? (
            <StatusChip tone="slate">Locked</StatusChip>
          ) : (
            <StatusChip tone="accent">In progress</StatusChip>
          )
        }
      />
      <div className="flex flex-col gap-4 px-[18px] py-4">
        {disabled && (
          <Alert tone="info">
            Generate this round&apos;s template before importing bids.
          </Alert>
        )}

        {/* import mode — segmented control */}
        <fieldset className="flex flex-wrap items-center gap-3" disabled={disabled || busy}>
          <legend className="float-left mr-3 text-xs font-semibold text-text-muted">
            Import mode
          </legend>
          <div className="flex rounded-control border border-border bg-surface-muted p-[3px]">
            {MODES.map((m) => {
              const active = mode === m.value;
              return (
                <button
                  key={m.value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => {
                    setMode(m.value);
                    resetResults();
                  }}
                  disabled={disabled || busy}
                  className={cn(
                    "rounded-[6px] px-3.5 py-1.5 text-xs font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40 disabled:cursor-not-allowed",
                    active
                      ? "bg-surface-card text-brand-primary shadow-card"
                      : "text-text-subtle hover:text-text-muted",
                  )}
                >
                  {m.title}
                </button>
              );
            })}
          </div>
          <span className="text-xs text-text-faint">
            {MODES.find((m) => m.value === mode)?.hint}
          </span>
        </fieldset>

        {gate && <Alert tone="warning">{gate}</Alert>}
        {error && <Alert tone="error">{error}</Alert>}

        {/* dropzone-styled upload */}
        <div className="flex flex-col items-center gap-3 rounded-card border-2 border-dashed border-border bg-surface-subtle px-6 py-7 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-card bg-sealed-bg">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-brand-primary"
              aria-hidden
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
            </svg>
          </span>
          <div>
            <p className="text-sm font-bold text-text-strong">
              Drop a bid workbook here, or browse
            </p>
            <p className="mt-0.5 text-xs text-text-faint">
              .xlsx — bids + Capacity sheet ingest together
            </p>
          </div>
          <div className="flex w-full max-w-md flex-col gap-3 sm:flex-row sm:items-center">
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
        </div>

        {/* import results */}
        {imported && (
          <div className="overflow-hidden rounded-card border border-success/30 bg-success-bg">
            <div className="flex items-center gap-2 border-b border-success/20 px-4 py-3">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.4"
                className="text-success"
                aria-hidden
              >
                <path d="M20 6 9 17l-5-5" />
              </svg>
              <span className="text-sm font-bold text-success">
                Round {round} bids imported · audit event recorded (IMPORTED)
              </span>
            </div>
            <div className="px-4 py-3 text-sm text-text-muted">
              Imported{" "}
              <span className="font-display font-extrabold tabular-nums text-text-strong">
                {ingested}
              </span>{" "}
              bid line{ingested === 1 ? "" : "s"}. Review them in step 4 below.
            </div>
          </div>
        )}

        {/* flexible mapping proposal / exception surface */}
        {proposal && (
          <div className="flex flex-col gap-4 rounded-card border border-warning/30 bg-warning-bg/40 p-4">
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
