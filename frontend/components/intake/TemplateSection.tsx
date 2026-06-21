"use client";

import { useState } from "react";
import { ApiError, generateTemplate } from "@/lib/api";
import type { KanbanResponse, RunFile } from "@/lib/api";
import { Button, Panel, PanelHeader } from "@/components/ui";
import { Alert } from "./Alert";
import { RunFilesTable } from "./RunFilesTable";

export interface TemplateSectionProps {
  slug: string;
  round: number;
  files: RunFile[];
  disabled: boolean;
  onTemplateGenerated: (filename: string, kanban: KanbanResponse) => void;
}

// Step 2 — generate the round's bid template, then download it from the files list.
export function TemplateSection({
  slug,
  round,
  files,
  disabled,
  onTemplateGenerated,
}: TemplateSectionProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gate, setGate] = useState<string | null>(null);
  const [lastFilename, setLastFilename] = useState<string | null>(null);

  // The generated template lands in inputs/ (not outputs/), so show THIS round's template from the
  // input files — it persists across a reload, unlike the session-only lastFilename.
  const templateFiles = files.filter(
    (f) => f.kind === "input" && f.name.includes(`round${round}_bid_template`),
  );

  async function onGenerate() {
    setError(null);
    setGate(null);
    setSubmitting(true);
    try {
      const result = await generateTemplate(slug, round);
      setLastFilename(result.filename);
      onTemplateGenerated(result.filename, result.kanban);
    } catch (err) {
      if (err instanceof ApiError && err.isGateRequired) {
        setGate(err.detail || "Complete setup before generating the template.");
      } else {
        setError(
          err instanceof ApiError
            ? err.detail || "Could not generate the template."
            : "Unexpected error generating the template.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel>
      <PanelHeader
        title="2 · Bid template"
        description={`Generate the round ${round} bid template for suppliers, then download it.`}
        actions={
          <Button
            onClick={() => void onGenerate()}
            loading={submitting}
            disabled={disabled}
          >
            Generate template
          </Button>
        }
      />
      <div className="flex flex-col gap-4 px-5 py-5">
        {disabled && (
          <Alert tone="info">
            Complete setup first to generate this round&apos;s template.
          </Alert>
        )}
        {gate && <Alert tone="warning">{gate}</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
        {lastFilename && !error && !gate && (
          <Alert tone="success">
            Template generated ·{" "}
            <code className="rounded bg-white/60 px-1.5 py-0.5 text-xs">
              {lastFilename}
            </code>
          </Alert>
        )}

        <RunFilesTable
          slug={slug}
          files={templateFiles}
          emptyLabel="No generated template yet — generate one above."
        />
      </div>
    </Panel>
  );
}
