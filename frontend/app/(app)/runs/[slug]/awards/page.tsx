"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  downloadRunFile,
  getAward,
  getRun,
  listAwards,
  recordAdjustment,
} from "@/lib/api";
import type {
  AwardDetail,
  AwardSummary,
  RecordAdjustmentBody,
  RunDetail,
} from "@/lib/api";
import { Button, Panel } from "@/components/ui";
import { Alert } from "@/components/intake/Alert";
import { AwardsListPanel } from "@/components/awards/AwardsListPanel";
import { AwardDetailPanel } from "@/components/awards/AwardDetailPanel";
import { RecordAdjustmentModal } from "@/components/awards/RecordAdjustmentModal";

// The post-award screen — view a run's frozen awards and inspect one: its awarded
// lines (frozen baseline → current effective price) and the versioned layer history.
// Read-only; the governed freeze lives on the alignment screen.
export default function AwardsPage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;

  const [run, setRun] = useState<RunDetail | null>(null);
  const [runErr, setRunErr] = useState<{ message: string; notFound: boolean } | null>(null);
  const [runLoading, setRunLoading] = useState(true);

  const [awards, setAwards] = useState<AwardSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [detail, setDetail] = useState<AwardDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  // Bumped after a recorded adjustment to re-fetch the (now-superseded) detail.
  const [reloadNonce, setReloadNonce] = useState(0);

  // Record-adjustment flow.
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [adjusting, setAdjusting] = useState(false);
  const [adjustError, setAdjustError] = useState<string | null>(null);
  const [adjustNotice, setAdjustNotice] = useState<{
    version: number;
    filename: string;
  } | null>(null);

  const loadRun = useCallback(async () => {
    setRunLoading(true);
    setRunErr(null);
    try {
      setRun(await getRun(slug));
    } catch (err) {
      if (err instanceof ApiError) {
        setRunErr({
          message:
            err.status === 404
              ? "This run could not be found."
              : err.detail || "Could not load this run.",
          notFound: err.status === 404,
        });
      } else {
        setRunErr({ message: "Unexpected error loading this run.", notFound: false });
      }
    } finally {
      setRunLoading(false);
    }
  }, [slug]);

  const loadAwards = useCallback(async () => {
    try {
      const rows = await listAwards(slug);
      setAwards(rows);
      setSelectedId((current) => {
        if (current && rows.some((r) => r.award_id === current)) return current;
        return rows.length ? rows[rows.length - 1].award_id : null;
      });
    } catch {
      // A failing list is non-fatal (e.g. no cycle / no award yet) — render as empty.
      setAwards([]);
      setSelectedId(null);
    }
  }, [slug]);

  useEffect(() => {
    void loadRun();
  }, [loadRun]);

  useEffect(() => {
    void loadAwards();
  }, [loadAwards]);

  // Load the selected award's detail. Race-safe: clear synchronously on change, and
  // only the live (non-aborted) request resolves the loading state.
  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    const ctrl = new AbortController();
    setDetail(null);
    setDetailLoading(true);
    setDetailError(null);
    getAward(slug, selectedId, ctrl.signal)
      .then((d) => {
        setDetail(d);
        setDetailLoading(false);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setDetail(null);
        setDetailError(err instanceof ApiError ? err.detail : "Could not load this award.");
        setDetailLoading(false);
      });
    return () => ctrl.abort();
  }, [slug, selectedId, reloadNonce]);

  // Selecting a different award clears any prior adjustment notice/error.
  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
    setAdjustNotice(null);
    setAdjustError(null);
  }, []);

  const handleAdjustConfirm = useCallback(
    async (body: RecordAdjustmentBody) => {
      if (!selectedId) return;
      setAdjusting(true);
      setAdjustError(null);
      try {
        const res = await recordAdjustment(slug, selectedId, body);
        setAdjustNotice({ version: res.version_no, filename: res.filename });
        setAdjustOpen(false);
        setReloadNonce((n) => n + 1); // re-fetch the now-updated award detail
        await loadAwards(); // the list's latest_version advances
      } catch (err) {
        setAdjustError(
          err instanceof ApiError ? err.detail : "Could not record the adjustment.",
        );
      } finally {
        setAdjusting(false);
      }
    },
    [slug, selectedId, loadAwards],
  );

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
        <span className="text-ink">Awards</span>
      </nav>

      {runLoading && (
        <Panel>
          <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-ink-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
            Loading run…
          </div>
        </Panel>
      )}

      {!runLoading && runErr && (
        <Panel>
          <div className="px-5 py-16 text-center">
            <p className="text-sm font-medium text-ink">
              {runErr.notFound ? "Run not found" : "Something went wrong"}
            </p>
            <p className="mt-1 text-sm text-ink-muted">{runErr.message}</p>
            <div className="mt-4 flex justify-center gap-2">
              {!runErr.notFound && (
                <Button variant="secondary" size="sm" onClick={() => void loadRun()}>
                  Retry
                </Button>
              )}
              <Link href={`/runs/${slug}`}>
                <Button variant={runErr.notFound ? "secondary" : "ghost"} size="sm">
                  Back to run
                </Button>
              </Link>
            </div>
          </div>
        </Panel>
      )}

      {!runLoading && !runErr && run && (
        <>
          <Panel className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <h1 className="text-xl font-semibold text-ink">Awards</h1>
                <p className="mt-1 text-sm text-ink-muted">
                  {run.commodity} · {run.label}
                </p>
              </div>
              <div className="flex gap-2">
                <Link href={`/runs/${slug}/alignment`}>
                  <Button variant="secondary" size="sm">
                    Alignment
                  </Button>
                </Link>
                <Link href={`/runs/${slug}`}>
                  <Button variant="secondary" size="sm">
                    Back to run
                  </Button>
                </Link>
              </div>
            </div>
          </Panel>

          <AwardsListPanel awards={awards} selectedId={selectedId} onSelect={handleSelect} />

          {selectedId && (
            <>
              {detailLoading && (
                <Panel>
                  <div className="flex items-center justify-center gap-3 px-5 py-12 text-sm text-ink-muted">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
                    Loading award…
                  </div>
                </Panel>
              )}
              {!detailLoading && detailError && <Alert tone="error">{detailError}</Alert>}
              {!detailLoading && !detailError && detail && detail.award_id === selectedId && (
                <>
                  {adjustNotice && (
                    <Alert tone="success">
                      Recorded adjustment v{adjustNotice.version}.{" "}
                      <button
                        type="button"
                        onClick={() => void downloadRunFile(slug, adjustNotice.filename)}
                        className="font-medium underline hover:no-underline"
                      >
                        Download the updated post-award document
                      </button>
                      .
                    </Alert>
                  )}
                  <AwardDetailPanel
                    detail={detail}
                    onAdjust={() => {
                      setAdjustError(null);
                      setAdjustNotice(null);
                      setAdjustOpen(true);
                    }}
                  />
                  <RecordAdjustmentModal
                    open={adjustOpen}
                    onClose={() => setAdjustOpen(false)}
                    onConfirm={handleAdjustConfirm}
                    submitting={adjusting}
                    error={adjustError}
                    awardCode={detail.award_code}
                    lines={detail.lines}
                  />
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
