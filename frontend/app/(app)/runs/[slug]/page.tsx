"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, getRun } from "@/lib/api";
import type { RunDetail } from "@/lib/api";
import { Button, Panel, StatusChip, stageTone } from "@/components/ui";
import { KanbanBoard } from "@/components/runs/KanbanBoard";
import { DownloadArchiveButton } from "@/components/intake/DownloadArchiveButton";

export default function RunDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  // Next 14 App Router: params is a plain object in Client Components.
  const { slug } = params;

  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<{ message: string; notFound: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRun(slug);
      setRun(data);
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

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-5">
      <nav className="text-sm text-ink-muted">
        <Link href="/" className="hover:text-accent">
          Runs
        </Link>
        <span className="px-1.5 text-ink-subtle">/</span>
        <span className="text-ink">{run?.commodity ?? slug}</span>
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
                <Button variant="secondary" size="sm" onClick={() => void load()}>
                  Retry
                </Button>
              )}
              <Link href="/">
                <Button variant={error.notFound ? "secondary" : "ghost"} size="sm">
                  Back to runs
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
                  <h1 className="text-xl font-semibold text-ink">{run.commodity}</h1>
                  {run.rehearsal && <StatusChip tone="amber">Rehearsal</StatusChip>}
                </div>
                <p className="mt-1 text-sm text-ink-muted">{run.label}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xs uppercase tracking-wide text-ink-subtle">
                    Stage
                  </span>
                  <StatusChip tone={stageTone(run.stage)}>{run.stage}</StatusChip>
                </div>
                <code className="rounded bg-surface-muted px-1.5 py-0.5 text-xs text-ink-muted">
                  {run.slug}
                </code>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-end gap-2 border-t border-line pt-4">
              <DownloadArchiveButton slug={run.slug} size="sm" />
              <Link href={`/runs/${run.slug}/intake`}>
                <Button variant="secondary" size="sm">
                  Bid intake
                </Button>
              </Link>
              <Link href={`/runs/${run.slug}/alignment`}>
                <Button variant="secondary" size="sm">
                  Alignment
                </Button>
              </Link>
              <Link href={`/runs/${run.slug}/awards`}>
                <Button size="sm">Awards</Button>
              </Link>
            </div>
          </Panel>

          <div>
            <h2 className="mb-3 text-sm font-semibold text-ink">Board</h2>
            <KanbanBoard kanban={run.kanban} />
          </div>
        </>
      )}
    </div>
  );
}
