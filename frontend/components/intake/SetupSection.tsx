"use client";

import { useState } from "react";
import { ApiError, uploadSetup } from "@/lib/api";
import type { KanbanResponse, RunFile } from "@/lib/api";
import { Button, FileInput, Panel, PanelHeader } from "@/components/ui";
import { Alert } from "./Alert";
import { RunFilesTable } from "./RunFilesTable";

export interface SetupSectionProps {
  slug: string;
  files: RunFile[];
  filesLoading: boolean;
  filesError: string | null;
  // The most recent cycle id, if setup has already been run this session.
  cycleId: string | null;
  onSetupComplete: (cycleId: string, kanban: KanbanResponse) => void;
}

// Step 1 — list the run's input files (the setup/kickoff workbook to download),
// then upload the filled workbook.
export function SetupSection({
  slug,
  files,
  filesLoading,
  filesError,
  cycleId,
  onSetupComplete,
}: SetupSectionProps) {
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inputFiles = files.filter((f) => f.kind === "input");

  async function onUpload() {
    if (!file) return;
    setError(null);
    setSubmitting(true);
    try {
      const result = await uploadSetup(slug, file);
      setFile(null);
      onSetupComplete(result.cycle_id, result.kanban);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail || "Could not process the setup workbook."
          : "Unexpected error uploading the setup workbook.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel>
      <PanelHeader
        title="1 · Setup"
        description="Download the kickoff workbook, fill it in, then upload it to open the sourcing cycle."
      />
      <div className="flex flex-col gap-4 px-5 py-5">
        {filesLoading ? (
          <div className="flex items-center justify-center gap-3 py-8 text-sm text-ink-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
            Loading files…
          </div>
        ) : filesError ? (
          <Alert tone="error">{filesError}</Alert>
        ) : (
          <RunFilesTable
            slug={slug}
            files={inputFiles}
            emptyLabel="No setup workbook found for this run yet."
          />
        )}

        <div className="flex flex-col gap-2 border-t border-line pt-4">
          <p className="text-sm font-medium text-ink">Upload filled workbook</p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <FileInput
              file={file}
              onChange={setFile}
              accept=".xlsx"
              disabled={submitting}
              className="sm:flex-1"
              buttonLabel="Choose .xlsx"
            />
            <Button
              onClick={() => void onUpload()}
              loading={submitting}
              disabled={!file}
            >
              Upload setup
            </Button>
          </div>

          {error && <Alert tone="error">{error}</Alert>}
          {cycleId && !error && (
            <Alert tone="success">
              Cycle opened ·{" "}
              <code className="rounded bg-white/60 px-1.5 py-0.5 text-xs">
                {cycleId}
              </code>
            </Alert>
          )}
        </div>
      </div>
    </Panel>
  );
}
