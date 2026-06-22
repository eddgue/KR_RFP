"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, getRun, KANBAN_BUCKETS } from "@/lib/api";
import type { Kanban, KanbanBucket, KanbanCard, RunDetail } from "@/lib/api";
import { Button, Panel, StatusChip, stageTone } from "@/components/ui";
import { RunStatusStrip } from "@/components/shell/RunStatusStrip";
import type { StatusCell, StatusTone } from "@/components/shell/RunStatusStrip";
import { DownloadArchiveButton } from "@/components/intake/DownloadArchiveButton";
import { cn } from "@/lib/cn";

// ── Lifecycle stepper ──────────────────────────────────────────────────────
// The five governed stages, in order. The current stage is derived from the
// run's free-form `stage` string (no extra API calls — behaviour unchanged).
const LIFECYCLE = [
  { key: "setup", label: "Setup", sub: "Cycle created" },
  { key: "intake", label: "Intake", sub: "Supplier bids loaded" },
  { key: "analysis", label: "Analysis", sub: "Sealed for review" },
  { key: "award", label: "Award", sub: "Frozen scenario" },
  { key: "close", label: "Close", sub: "Run finalised" },
] as const;

function stageIndex(stage: string, hasCycle: boolean): number {
  const s = stage.toLowerCase();
  if (/(close|final|complete|done)/.test(s)) return 4;
  if (/(post[- ]?award|award|frozen)/.test(s)) return 3;
  if (/(analy|seal|align|scenario)/.test(s)) return 2;
  if (/(intake|bid|round|import|load)/.test(s)) return 1;
  if (/(setup|kickoff|cycle)/.test(s) || hasCycle) return 0;
  return 0;
}

// ── Run-status strip derivation ────────────────────────────────────────────
function statusCells(run: RunDetail): StatusCell[] {
  const idx = stageIndex(run.stage, run.has_cycle);

  const runTone: StatusTone = idx >= 4 ? "idle" : "live";
  const analysisDone = idx >= 2;
  const awardDone = idx >= 3;

  return [
    { label: "RUN STATE", value: run.stage, tone: runTone },
    {
      label: "ANALYSIS",
      value: analysisDone ? "Sealed" : "—",
      tone: analysisDone ? "sealed" : "idle",
    },
    {
      label: "AWARD",
      value: awardDone ? "Frozen" : "Not frozen",
      tone: awardDone ? "frozen" : "idle",
    },
    { label: "AUDIT", value: "Current", tone: "live" },
  ];
}

// ── Activity board (re-skin of the existing kanban data) ────────────────────
const BUCKET_DOT: Record<KanbanBucket, string> = {
  Done: "bg-success",
  Doing: "bg-brand-sky",
  Next: "bg-text-faint",
  "Waiting on you": "bg-warning",
};

function cardTitle(card: KanbanCard): string {
  if (typeof card === "string") return card;
  return (
    (card.title ?? card.label ?? (typeof card.id === "string" ? card.id : "")) ||
    "Untitled item"
  );
}

function cardKey(card: KanbanCard, i: number): string {
  if (typeof card === "string") return `${i}:${card}`;
  if (typeof card.id === "string") return card.id;
  return `${i}:${cardTitle(card)}`;
}

function ActivityBoard({ kanban }: { kanban: Kanban }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {KANBAN_BUCKETS.map((bucket) => {
        const cards = kanban[bucket] ?? [];
        const isWaiting = bucket === "Waiting on you";
        return (
          <div
            key={bucket}
            className="overflow-hidden rounded-card border border-border bg-surface-card"
          >
            <div className="flex items-center justify-between gap-2 border-b border-border-hairline px-3.5 py-2.5">
              <div className="flex items-center gap-2">
                <span
                  className={cn("h-2 w-2 rounded-full", BUCKET_DOT[bucket])}
                  aria-hidden
                />
                <span className="text-sm font-semibold text-text-strong">
                  {bucket}
                </span>
              </div>
              <span className="rounded-control bg-surface-muted px-2 py-0.5 text-2xs font-bold tabular-nums text-text-muted">
                {cards.length}
              </span>
            </div>
            <div className="flex flex-col gap-2 p-2.5">
              {cards.length === 0 ? (
                <p className="px-1 py-5 text-center text-xs text-text-subtle">
                  No items
                </p>
              ) : (
                cards.map((card, i) => (
                  <div
                    key={cardKey(card, i)}
                    className={cn(
                      "rounded-control border px-3 py-2.5 text-sm font-semibold leading-snug text-text-muted",
                      isWaiting
                        ? "border-warning/30 bg-warning-bg"
                        : "border-border-hairline bg-surface-subtle",
                    )}
                  >
                    {cardTitle(card)}
                  </div>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

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

  const currentStage = run ? stageIndex(run.stage, run.has_cycle) : 0;

  return (
    <div className="flex flex-col gap-[18px]">
      <nav className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/" className="hover:text-brand-primary">
          Runs
        </Link>
        <span className="text-text-faint">/</span>
        <span className="font-bold text-text-strong">{run?.commodity ?? slug}</span>
      </nav>

      {loading && (
        <Panel>
          <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-text-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-border-hairline border-t-brand-primary" />
            Loading run…
          </div>
        </Panel>
      )}

      {!loading && error && (
        <Panel>
          <div className="px-5 py-16 text-center">
            <p className="text-sm font-semibold text-text-strong">
              {error.notFound ? "Run not found" : "Something went wrong"}
            </p>
            <p className="mt-1 text-sm text-text-muted">{error.message}</p>
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
          {/* persistent run-status strip */}
          <RunStatusStrip cells={statusCells(run)} />

          {/* run header */}
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3.5">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-card bg-danger-bg font-display text-xl font-extrabold text-danger">
                {run.commodity.charAt(0).toUpperCase()}
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1 className="text-2xl font-extrabold tracking-tight text-text-strong">
                    {run.commodity}
                  </h1>
                  {run.rehearsal && <StatusChip tone="amber">Rehearsal</StatusChip>}
                  {currentStage >= 3 && (
                    <StatusChip tone="frozen">Post-award</StatusChip>
                  )}
                </div>
                <p className="mt-0.5 text-sm text-text-muted">
                  {run.label}
                  <span className="px-2 text-text-faint">·</span>
                  <code className="font-display text-xs text-text-faint">
                    {run.slug}
                  </code>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <DownloadArchiveButton slug={run.slug} size="sm" />
              <Link href={`/runs/${run.slug}/alignment`}>
                <Button size="sm">Open alignment</Button>
              </Link>
            </div>
          </div>

          {/* lifecycle stepper */}
          <Panel className="px-5 py-[18px]">
            <p className="mb-4 text-2xs font-bold uppercase tracking-wider text-text-subtle">
              Sourcing lifecycle
            </p>
            <ol className="flex items-start">
              {LIFECYCLE.map((stage, i) => {
                const done = i < currentStage;
                const current = i === currentStage;
                return (
                  <li
                    key={stage.key}
                    className="relative flex flex-1 flex-col items-center text-center"
                  >
                    {i > 0 && (
                      <span
                        className={cn(
                          "absolute top-[15px] h-0.5",
                          i <= currentStage ? "bg-success" : "bg-border",
                        )}
                        style={{ left: "calc(-50% + 16px)", right: "calc(50% + 16px)" }}
                        aria-hidden
                      />
                    )}
                    <span
                      className={cn(
                        "relative z-[1] flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-extrabold tabular-nums",
                        done && "border-success bg-success text-white",
                        current &&
                          "border-brand-primary bg-sealed-bg text-brand-primary",
                        !done &&
                          !current &&
                          "border-border bg-surface-card text-text-faint",
                      )}
                    >
                      {done ? "✓" : i + 1}
                    </span>
                    <span
                      className={cn(
                        "mt-2 text-sm font-bold",
                        done || current ? "text-text-strong" : "text-text-faint",
                      )}
                    >
                      {stage.label}
                    </span>
                    <span className="mt-0.5 max-w-[150px] text-2xs text-text-faint">
                      {stage.sub}
                    </span>
                  </li>
                );
              })}
            </ol>
          </Panel>

          {/* two-column: activity board + decision/next-step rail */}
          <div className="flex flex-col gap-[18px] lg:flex-row lg:items-start">
            <div className="min-w-0 flex-1">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h2 className="text-base font-bold text-text-strong">
                  Activity board
                </h2>
                <span className="text-xs text-text-subtle">
                  What&apos;s done, in progress, and waiting on you
                </span>
              </div>
              <ActivityBoard kanban={run.kanban} />
            </div>

            <div className="flex w-full flex-none flex-col gap-4 lg:w-[320px]">
              {/* run facts */}
              <Panel className="overflow-hidden">
                <div className="border-b border-border-hairline px-4 py-3">
                  <h3 className="text-sm font-bold text-text-strong">Run facts</h3>
                </div>
                <dl className="px-4 py-1.5">
                  {[
                    { k: "Commodity", v: run.commodity },
                    { k: "Cycle", v: run.label },
                    { k: "Stage", v: run.stage },
                    { k: "Mode", v: run.rehearsal ? "Rehearsal" : "Production" },
                    { k: "Run ID", v: run.slug },
                  ].map((f) => (
                    <div
                      key={f.k}
                      className="flex items-start justify-between gap-4 border-b border-border-hairline py-2 last:border-0"
                    >
                      <dt className="shrink-0 text-sm font-semibold text-text-subtle">
                        {f.k}
                      </dt>
                      <dd className="text-right text-sm font-bold text-text-strong">
                        {f.v}
                      </dd>
                    </div>
                  ))}
                </dl>
              </Panel>

              {/* next steps */}
              <Panel className="overflow-hidden">
                <div className="border-b border-border-hairline px-4 py-3">
                  <h3 className="text-sm font-bold text-text-strong">Next steps</h3>
                </div>
                <div className="flex flex-col gap-2 px-4 py-4">
                  <Link href={`/runs/${run.slug}/intake`} className="block">
                    <Button variant="secondary" size="sm" className="w-full justify-between">
                      Bid intake
                      <span aria-hidden>→</span>
                    </Button>
                  </Link>
                  <Link href={`/runs/${run.slug}/alignment`} className="block">
                    <Button variant="secondary" size="sm" className="w-full justify-between">
                      Alignment
                      <span aria-hidden>→</span>
                    </Button>
                  </Link>
                  <Link href={`/runs/${run.slug}/awards`} className="block">
                    <Button size="sm" className="w-full justify-between">
                      Awards
                      <span aria-hidden>→</span>
                    </Button>
                  </Link>
                </div>
              </Panel>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
