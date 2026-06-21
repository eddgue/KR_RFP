"use client";

import { useCallback, useEffect, useState } from "react";
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
import { NewRunModal } from "@/components/runs/NewRunModal";

function PlusIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

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

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-ink">Runs</h1>
          <p className="mt-0.5 text-sm text-ink-muted">
            Sourcing runs across all commodities.
          </p>
        </div>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon />
          New run
        </Button>
      </div>

      <Panel>
        <PanelHeader
          title="All runs"
          description={
            runs ? `${runs.length} run${runs.length === 1 ? "" : "s"}` : undefined
          }
        />

        {loading && (
          <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-ink-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
            Loading runs…
          </div>
        )}

        {!loading && error && (
          <div className="px-5 py-16 text-center">
            <p className="text-sm text-red-700">{error}</p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        )}

        {!loading && !error && runs && runs.length === 0 && (
          <div className="px-5 py-16 text-center">
            <p className="text-sm font-medium text-ink">No runs yet</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-ink-muted">
              Create your first sourcing run to start collecting and aligning bids.
            </p>
            <Button className="mt-4" onClick={() => setModalOpen(true)}>
              <PlusIcon />
              New run
            </Button>
          </div>
        )}

        {!loading && !error && runs && runs.length > 0 && (
          <Table>
            <THead>
              <TR>
                <TH>Commodity</TH>
                <TH>Label</TH>
                <TH>Stage</TH>
                <TH>Type</TH>
                <TH>Slug</TH>
              </TR>
            </THead>
            <TBody>
              {runs.map((run) => (
                <TR
                  key={run.slug}
                  onClick={() => router.push(`/runs/${run.slug}`)}
                >
                  <TD className="font-medium">{run.commodity}</TD>
                  <TD className="text-ink-muted">{run.label}</TD>
                  <TD>
                    <StatusChip tone={stageTone(run.stage)}>{run.stage}</StatusChip>
                  </TD>
                  <TD>
                    {run.rehearsal ? (
                      <StatusChip tone="amber">Rehearsal</StatusChip>
                    ) : (
                      <span className="text-2xs uppercase tracking-wide text-ink-subtle">
                        Production
                      </span>
                    )}
                  </TD>
                  <TD>
                    <code className="rounded bg-surface-muted px-1.5 py-0.5 text-xs text-ink-muted">
                      {run.slug}
                    </code>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
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
