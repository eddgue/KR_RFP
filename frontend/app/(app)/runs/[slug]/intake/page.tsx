"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, getRun, listRunFiles } from "@/lib/api";
import type { Kanban, RunDetail, RunFile } from "@/lib/api";
import { KANBAN_BUCKETS } from "@/lib/api";
import { Button, Panel, StatusChip, stageTone } from "@/components/ui";
import { KanbanBoard } from "@/components/runs/KanbanBoard";
import { SetupSection } from "@/components/intake/SetupSection";
import { TemplateSection } from "@/components/intake/TemplateSection";
import { ImportSection } from "@/components/intake/ImportSection";
import { ReviewSection } from "@/components/intake/ReviewSection";
import { DownloadArchiveButton } from "@/components/intake/DownloadArchiveButton";

// The loose Record<string,string[]> kanban returned by intake endpoints is
// normalized to the strict 4-bucket Kanban the board renders.
function normalizeKanban(raw: Record<string, string[]>): Kanban {
  const out = {} as Kanban;
  for (const bucket of KANBAN_BUCKETS) {
    out[bucket] = raw[bucket] ?? [];
  }
  return out;
}

const MAX_ROUND = 6;

export default function RunIntakePage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;

  const [run, setRun] = useState<RunDetail | null>(null);
  const [kanban, setKanban] = useState<Kanban | null>(null);
  const [error, setError] = useState<{ message: string; notFound: boolean } | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  const [files, setFiles] = useState<RunFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(true);
  const [filesError, setFilesError] = useState<string | null>(null);

  const [round, setRound] = useState(1);
  const [cycleId, setCycleId] = useState<string | null>(null);
  const [setupDoneThisSession, setSetupDoneThisSession] = useState(false);
  const [templateDoneThisSession, setTemplateDoneThisSession] = useState(false);
  const [bidsRefreshKey, setBidsRefreshKey] = useState(0);

  // Soft gating: the backend is the source of truth (it returns `gate_required`
  // when a step is run too early). Locally we unlock a step from durable server
  // state or this session's progress. Setup-done is the run's `has_cycle` flag
  // (true once setup is ingested — works even for a returning user who hasn't
  // generated a template yet). Template-done is the round's template file in
  // inputs/ (a template implies the cycle exists too).
  const hasRoundTemplate = files.some(
    (f) => f.kind === "input" && f.name.includes(`round${round}_bid_template`),
  );
  const setupDone = setupDoneThisSession || Boolean(run?.has_cycle) || hasRoundTemplate;
  const templateDone = templateDoneThisSession || hasRoundTemplate;

  const loadRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRun(slug);
      setRun(data);
      setKanban(data.kanban);
    } catch (err) {
      if (err instanceof ApiError) {
        setError({
          message:
            err.status === 404
              ? "This run could not be found."
              : err.detail || "Could not load this run.",
          notFound: err.status === 404,
        });
      } else {
        setError({ message: "Unexpected error loading this run.", notFound: false });
      }
    } finally {
      setLoading(false);
    }
  }, [slug]);

  const loadFiles = useCallback(async () => {
    setFilesLoading(true);
    setFilesError(null);
    try {
      const data = await listRunFiles(slug);
      setFiles(data);
    } catch (err) {
      setFilesError(
        err instanceof ApiError
          ? err.detail || "Could not load run files."
          : "Unexpected error loading run files.",
      );
    } finally {
      setFilesLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    void loadRun();
    void loadFiles();
  }, [loadRun, loadFiles]);

  return (
    <div className="flex flex-col gap-5">
      <nav className="text-sm text-ink-muted">
        <Link href="/" className="hover:text-accent">
          Runs
        </Link>
        <span className="px-1.5 text-ink-subtle">/</span>
        <Link href={`/runs/${slug}`} className="hover:text-accent">
          {run?.commodity ?? slug}
        </Link>
        <span className="px-1.5 text-ink-subtle">/</span>
        <span className="text-ink">Bid intake</span>
      </nav>

      {loading && (
        <Panel>
          <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-ink-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
            Loading run…
          </div>
        </Panel>
      )}

      {!loading && error && (
        <Panel>
          <div className="px-5 py-16 text-center">
            <p className="text-sm font-medium text-ink">
              {error.notFound ? "Run not found" : "Something went wrong"}
            </p>
            <p className="mt-1 text-sm text-ink-muted">{error.message}</p>
            <div className="mt-4 flex justify-center gap-2">
              {!error.notFound && (
                <Button variant="secondary" size="sm" onClick={() => void loadRun()}>
                  Retry
                </Button>
              )}
              <Link href={`/runs/${slug}`}>
                <Button variant="ghost" size="sm">
                  Back to run
                </Button>
              </Link>
            </div>
          </div>
        </Panel>
      )}

      {!loading && !error && run && (
        <>
          <Panel className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold text-ink">
                    {run.commodity}
                  </h1>
                  {run.rehearsal && <StatusChip tone="amber">Rehearsal</StatusChip>}
                  <StatusChip tone={stageTone(run.stage)}>{run.stage}</StatusChip>
                </div>
                <p className="mt-1 text-sm text-ink-muted">
                  {run.label} · Bid intake
                </p>
              </div>
              <div className="flex flex-col items-end gap-3">
                <DownloadArchiveButton slug={slug} />
                <div className="flex items-center gap-2">
                  <label
                    htmlFor="round-select"
                    className="text-2xs uppercase tracking-wide text-ink-subtle"
                  >
                    Round
                  </label>
                  <select
                    id="round-select"
                    value={round}
                    onChange={(e) => {
                      setRound(Number(e.target.value));
                      // Round-scoped progress resets when switching rounds.
                      setTemplateDoneThisSession(false);
                    }}
                    className="h-8 rounded-md border border-line-strong bg-white px-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/40"
                  >
                    {Array.from({ length: MAX_ROUND }, (_, i) => i + 1).map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </Panel>

          <SetupSection
            slug={slug}
            files={files}
            filesLoading={filesLoading}
            filesError={filesError}
            cycleId={cycleId}
            onSetupComplete={(id, raw) => {
              setCycleId(id);
              setSetupDoneThisSession(true);
              setKanban(normalizeKanban(raw));
              void loadFiles();
            }}
          />

          <TemplateSection
            slug={slug}
            round={round}
            files={files}
            disabled={!setupDone}
            onTemplateGenerated={(_filename, raw) => {
              setTemplateDoneThisSession(true);
              setKanban(normalizeKanban(raw));
              void loadFiles();
            }}
          />

          <ImportSection
            slug={slug}
            round={round}
            disabled={!templateDone}
            onImported={(_ingested, raw) => {
              setKanban(normalizeKanban(raw));
              setBidsRefreshKey((k) => k + 1);
              void loadFiles();
            }}
          />

          <ReviewSection slug={slug} round={round} refreshKey={bidsRefreshKey} />

          {kanban && (
            <div>
              <h2 className="mb-3 text-sm font-semibold text-ink">Board</h2>
              <KanbanBoard kanban={kanban} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
