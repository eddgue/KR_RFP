"use client";

import { useState } from "react";
import { ApiError, downloadRunFile } from "@/lib/api";
import type { RunFile } from "@/lib/api";
import {
  Button,
  StatusChip,
  Table,
  THead,
  TBody,
  TR,
  TH,
  TD,
} from "@/components/ui";
import { formatBytes, formatTimestamp } from "@/lib/format";
import { Alert } from "./Alert";

export interface RunFilesTableProps {
  slug: string;
  files: RunFile[];
  // Optional filter — e.g. only show input or output files.
  emptyLabel?: string;
}

// A compact table of run-folder files, each with an authenticated download.
export function RunFilesTable({ slug, files, emptyLabel }: RunFilesTableProps) {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function download(name: string) {
    setError(null);
    setDownloading(name);
    try {
      await downloadRunFile(slug, name);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail || `Could not download ${name}.`
          : `Could not download ${name}.`,
      );
    } finally {
      setDownloading(null);
    }
  }

  if (files.length === 0) {
    return (
      <p className="px-1 py-6 text-center text-sm text-ink-subtle">
        {emptyLabel ?? "No files yet."}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error && <Alert tone="error">{error}</Alert>}
      <Table>
        <THead>
          <TR>
            <TH>File</TH>
            <TH>Kind</TH>
            <TH className="text-right">Size</TH>
            <TH>Modified</TH>
            <TH className="text-right">Action</TH>
          </TR>
        </THead>
        <TBody>
          {files.map((f) => (
            <TR key={f.name}>
              <TD className="font-medium">{f.name}</TD>
              <TD>
                <StatusChip tone={f.kind === "output" ? "accent" : "slate"}>
                  {f.kind}
                </StatusChip>
              </TD>
              <TD className="text-right tabular-nums text-ink-muted">
                {formatBytes(f.size_bytes)}
              </TD>
              <TD className="text-ink-muted">{formatTimestamp(f.modified)}</TD>
              <TD className="text-right">
                <Button
                  variant="secondary"
                  size="sm"
                  loading={downloading === f.name}
                  disabled={downloading !== null && downloading !== f.name}
                  onClick={() => void download(f.name)}
                >
                  Download
                </Button>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
