"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, listRuns } from "@/lib/api";
import type { RunSummary } from "@/lib/api";
import {
  Button,
  Panel,
  PanelHeader,
  StatusChip,
  stageTone,
  Table,
  THead,
  TBody,
  TR,
  TH,
  TD,
} from "@/components/ui";
import { formatCount } from "@/lib/format";
import { NewRunModal } from "@/components/runs/NewRunModal";

function PlusIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4-4" strokeLinecap="round" />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden>
      <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// A run is "closed" once its stage reads as awarded/closed/done — used for the
// active-runs KPI and the muted progress bar.
function isClosedStage(stage: string): boolean {
  return /(done|complete|award|closed|archiv)/i.test(stage);
}

// One small metric card for the KPI strip. Numbers render in the display face.
function MetricCard({
  label,
  value,
  sub,
  tone = "strong",
}: {
  label: string;
  value: string;
  sub: string;
  tone?: "strong" | "warning" | "success";
}) {
  const valueTone =
    tone === "warning"
      ? "text-warning"
      : tone === "success"
        ? "text-success"
        : "text-text-strong";
  return (
    <div className="rounded-card border border-border bg-surface-card px-4 py-3.5 shadow-card">
      <div className="mb-1.5 text-xs font-semibold text-text-subtle">{label}</div>
      <div className="flex items-baseline gap-2">
        <span className={`font-display text-2xl font-extrabold tabular-nums ${valueTone}`}>
          {value}
        </span>
        <span className="text-xs font-semibold text-text-subtle">{sub}</span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listRuns();
      setRuns(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail || "Could not load runs."
          : "Unexpected error loading runs.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // The visible (filtered) set. All totals/counts below reflect THIS set, not the
  // full list — per the locked interaction rule.
  const filtered = useMemo(() => {
    const list = runs ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter((r) =>
      `${r.commodity} ${r.label} ${r.stage} ${r.slug}`.toLowerCase().includes(q),
    );
  }, [runs, query]);

  const kpis = useMemo(() => {
    const active = filtered.filter((r) => !isClosedStage(r.stage)).length;
    const rehearsal = filtered.filter((r) => r.rehearsal).length;
    const production = filtered.filter((r) => !r.rehearsal).length;
    return {
      total: filtered.length,
      active,
      rehearsal,
      production,
    };
  }, [filtered]);

  const hasRuns = runs !== null && runs.length > 0;

  return (
    <div className="flex flex-col gap-5">
      {/* page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-text-strong">
            Sourcing runs
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Every produce RFP cycle across commodities. Open a run to set up bids,
            align scenarios, and freeze awards.
          </p>
        </div>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon />
          New run
        </Button>
      </div>

      {/* KPI strip — counts reflect the filtered set */}
      {hasRuns && !error && (
        <div className="grid grid-cols-2 gap-3.5 xl:grid-cols-4">
          <MetricCard
            label={query.trim() ? "Matching runs" : "Total runs"}
            value={formatCount(kpis.total)}
            sub={query.trim() ? "in view" : "tracked"}
          />
          <MetricCard
            label="Active runs"
            value={formatCount(kpis.active)}
            sub="in flight"
            tone="warning"
          />
          <MetricCard
            label="Production runs"
            value={formatCount(kpis.production)}
            sub="governed"
            tone="success"
          />
          <MetricCard
            label="Rehearsal runs"
            value={formatCount(kpis.rehearsal)}
            sub="practice"
          />
        </div>
      )}

      <Panel>
        <PanelHeader
          title={
            <span className="flex items-center gap-2.5">
              All runs
              {hasRuns && !error && (
                <span className="rounded bg-surface-muted px-2 py-0.5 text-2xs font-bold tabular-nums text-text-muted">
                  {formatCount(filtered.length)}
                </span>
              )}
            </span>
          }
          actions={
            hasRuns && !error ? (
              <div className="flex w-[240px] items-center gap-2 rounded-control border border-border bg-surface-subtle px-3 py-1.5 focus-within:border-brand-sky">
                <span className="text-text-subtle">
                  <SearchIcon />
                </span>
                <input
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search commodity, cycle, stage"
                  aria-label="Search runs"
                  className="w-full border-none bg-transparent text-sm text-text outline-none placeholder:text-text-subtle"
                />
              </div>
            ) : undefined
          }
        />

        {loading && (
          <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-text-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-border-hairline border-t-brand-primary" />
            Loading runs…
          </div>
        )}

        {!loading && error && (
          <div className="px-5 py-16 text-center">
            <p className="text-sm text-danger">{error}</p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        )}

        {!loading && !error && runs && runs.length === 0 && (
          <div className="px-5 py-16 text-center">
            <p className="text-sm font-semibold text-text-strong">No runs yet</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-text-muted">
              Create your first sourcing run to start collecting and aligning bids.
            </p>
            <Button className="mt-4" onClick={() => setModalOpen(true)}>
              <PlusIcon />
              New run
            </Button>
          </div>
        )}

        {!loading && !error && hasRuns && (
          <>
            <Table>
              <THead>
                <TR>
                  <TH>Commodity</TH>
                  <TH>Cycle</TH>
                  <TH>Type</TH>
                  <TH className="w-[260px]">Stage</TH>
                  <TH className="w-10">
                    <span className="sr-only">Open</span>
                  </TH>
                </TR>
              </THead>
              <TBody>
                {filtered.map((run) => {
                  const closed = isClosedStage(run.stage);
                  return (
                    <TR
                      key={run.slug}
                      onClick={() => router.push(`/runs/${run.slug}`)}
                    >
                      <TD>
                        <div className="flex items-center gap-3">
                          <span className="flex h-8 w-8 flex-none items-center justify-center rounded-control bg-accent-soft font-display text-sm font-extrabold text-brand-primary">
                            {run.commodity.slice(0, 1).toUpperCase()}
                          </span>
                          <span className="font-semibold text-text">{run.commodity}</span>
                        </div>
                      </TD>
                      <TD className="font-medium text-text-muted">{run.label}</TD>
                      <TD>
                        {run.rehearsal ? (
                          <StatusChip tone="amber">Rehearsal</StatusChip>
                        ) : (
                          <span className="text-2xs font-semibold uppercase tracking-wide text-text-subtle">
                            Production
                          </span>
                        )}
                      </TD>
                      <TD>
                        <div className="flex flex-col gap-1.5">
                          <StatusChip tone={stageTone(run.stage)}>{run.stage}</StatusChip>
                          <span
                            className="h-1 w-full overflow-hidden rounded-pill bg-surface-muted"
                            aria-hidden
                          >
                            <span
                              className={`block h-full rounded-pill ${
                                closed ? "w-full bg-success/40" : "w-1/2 bg-brand-sky"
                              }`}
                            />
                          </span>
                        </div>
                      </TD>
                      <TD className="text-right text-text-faint">
                        <ChevronIcon />
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>

            {filtered.length === 0 && (
              <div className="px-5 py-14 text-center text-sm text-text-subtle">
                No runs match “{query.trim()}”.
              </div>
            )}
          </>
        )}
      </Panel>

      <NewRunModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={(run) => {
          setModalOpen(false);
          // Refresh the table so the new row appears, then go to its detail.
          void load();
          router.push(`/runs/${run.slug}`);
        }}
      />
    </div>
  );
}
