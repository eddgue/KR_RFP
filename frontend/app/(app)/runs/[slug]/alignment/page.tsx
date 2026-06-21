"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  freezeAward,
  getRun,
  getScenarioComparison,
  getScenarioDetail,
  listAnalyses,
  runAnalysis,
} from "@/lib/api";
import type {
  AnalysisSummary,
  RunDetail,
  ScenarioComparisonRow,
  ScenarioDetail,
} from "@/lib/api";
import { Button, Panel } from "@/components/ui";
import { Alert } from "@/components/intake/Alert";
import { AnalysisRunsPanel } from "@/components/alignment/AnalysisRunsPanel";
import { ScenarioComparisonTable } from "@/components/alignment/ScenarioComparisonTable";
import { ScenarioDetailPanel } from "@/components/alignment/ScenarioDetailPanel";
import { FreezeAwardModal } from "@/components/alignment/FreezeAwardModal";

// The alignment / scenario screen — the centerpiece. Run a round's analysis, pick
// a sealed run, compare the seven lenses, inspect one cell-by-cell, and freeze the
// chosen lens into a governed award. All numbers come from the sealed engine
// records via the read layer (identical to the alignment workbook).
export default function AlignmentPage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;

  // Run header.
  const [run, setRun] = useState<RunDetail | null>(null);
  const [runErr, setRunErr] = useState<{ message: string; notFound: boolean } | null>(null);
  const [runLoading, setRunLoading] = useState(true);

  // Sealed analyses + the selected one.
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runAnalysisError, setRunAnalysisError] = useState<string | null>(null);

  // Scenario comparison for the selected analysis + the selected lens.
  const [comparison, setComparison] = useState<ScenarioComparisonRow[]>([]);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);

  // The selected lens, cell-by-cell.
  const [detail, setDetail] = useState<ScenarioDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Freeze flow.
  const [freezeOpen, setFreezeOpen] = useState(false);
  const [freezing, setFreezing] = useState(false);
  const [freezeError, setFreezeError] = useState<string | null>(null);
  const [frozen, setFrozen] = useState<Record<string, string>>({});

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

  const loadAnalyses = useCallback(
    async (selectId?: string) => {
      try {
        const rows = await listAnalyses(slug);
        setAnalyses(rows);
        setSelectedAnalysisId((current) => {
          if (selectId) return selectId;
          if (current && rows.some((r) => r.analysis_run_id === current)) return current;
          return rows.length ? rows[rows.length - 1].analysis_run_id : null;
        });
      } catch {
        // A failing list is non-fatal (e.g. no cycle yet) — render as "no analyses".
        setAnalyses([]);
        setSelectedAnalysisId(null);
      }
    },
    [slug],
  );

  useEffect(() => {
    void loadRun();
  }, [loadRun]);

  useEffect(() => {
    void loadAnalyses();
  }, [loadAnalyses]);

  // Load the comparison whenever the selected analysis changes; auto-select B.
  useEffect(() => {
    if (!selectedAnalysisId) {
      setComparison([]);
      setSelectedCode(null);
      return;
    }
    const ctrl = new AbortController();
    setComparisonLoading(true);
    setComparisonError(null);
    getScenarioComparison(slug, selectedAnalysisId, ctrl.signal)
      .then((rows) => {
        setComparison(rows);
        setSelectedCode((current) => {
          if (current && rows.some((r) => r.code === current)) return current;
          const rec = rows.find((r) => r.is_recommended) ?? rows[0];
          return rec ? rec.code : null;
        });
        setComparisonLoading(false);
      })
      .catch((err) => {
        // Aborted = a superseded analysis selection; the live request owns `loading`.
        if (err instanceof DOMException && err.name === "AbortError") return;
        setComparison([]);
        setComparisonError(
          err instanceof ApiError ? err.detail : "Could not load the scenarios.",
        );
        setComparisonLoading(false);
      });
    return () => ctrl.abort();
  }, [slug, selectedAnalysisId]);

  // Load the cell-by-cell detail whenever the selected lens changes.
  useEffect(() => {
    if (!selectedAnalysisId || !selectedCode) {
      setDetail(null);
      return;
    }
    const ctrl = new AbortController();
    // Clear the previous lens SYNCHRONOUSLY so a stale detail can never render against the
    // newly-selected code (which would let the freeze modal show lens A while posting lens B).
    setDetail(null);
    setDetailLoading(true);
    setDetailError(null);
    getScenarioDetail(slug, selectedAnalysisId, selectedCode, ctrl.signal)
      .then((d) => {
        setDetail(d);
        setDetailLoading(false);
      })
      .catch((err) => {
        // An aborted request belongs to a superseded selection — leave `loading` for the live one
        // (don't flip it false here, or the stale-but-cleared state would look "loaded").
        if (err instanceof DOMException && err.name === "AbortError") return;
        setDetail(null);
        setDetailError(
          err instanceof ApiError ? err.detail : "Could not load this scenario.",
        );
        setDetailLoading(false);
      });
    return () => ctrl.abort();
  }, [slug, selectedAnalysisId, selectedCode]);

  const handleRun = useCallback(
    async (round: number) => {
      setRunning(true);
      setRunAnalysisError(null);
      try {
        const res = await runAnalysis(slug, round);
        setSelectedCode(null);
        await loadAnalyses(res.analysis_run_id);
      } catch (err) {
        setRunAnalysisError(
          err instanceof ApiError ? err.detail : "Could not run the analysis.",
        );
      } finally {
        setRunning(false);
      }
    },
    [slug, loadAnalyses],
  );

  const handleSelectAnalysis = useCallback((id: string) => {
    setSelectedAnalysisId(id);
    setSelectedCode(null);
    setDetail(null);
  }, []);

  const handleFreezeConfirm = useCallback(
    async (awardCode: string) => {
      if (!selectedAnalysisId || !selectedCode) return;
      setFreezing(true);
      setFreezeError(null);
      try {
        const res = await freezeAward(slug, {
          analysis_run_id: selectedAnalysisId,
          scenario_code: selectedCode,
          award_code: awardCode,
        });
        setFrozen((prev) => ({
          ...prev,
          [`${selectedAnalysisId}:${selectedCode}`]: res.award_id,
        }));
        setFreezeOpen(false);
      } catch (err) {
        setFreezeError(
          err instanceof ApiError ? err.detail : "Could not freeze the award.",
        );
      } finally {
        setFreezing(false);
      }
    },
    [slug, selectedAnalysisId, selectedCode],
  );

  const frozenKey =
    selectedAnalysisId && selectedCode ? `${selectedAnalysisId}:${selectedCode}` : "";
  const frozenAwardId = frozenKey ? (frozen[frozenKey] ?? null) : null;

  const commoditySlug = run
    ? run.commodity
        .toUpperCase()
        .replace(/[^A-Z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 16)
    : "";
  const suggestedAwardCode = `AWD-${commoditySlug ? `${commoditySlug}-` : ""}${selectedCode ?? "B"}`;

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
        <span className="text-ink">Alignment</span>
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
                <h1 className="text-xl font-semibold text-ink">Alignment</h1>
                <p className="mt-1 text-sm text-ink-muted">
                  {run.commodity} · {run.label}
                </p>
              </div>
              <Link href={`/runs/${slug}`}>
                <Button variant="secondary" size="sm">
                  Back to run
                </Button>
              </Link>
            </div>
          </Panel>

          {runAnalysisError && <Alert tone="error">{runAnalysisError}</Alert>}

          <AnalysisRunsPanel
            analyses={analyses}
            selectedId={selectedAnalysisId}
            onSelect={handleSelectAnalysis}
            onRun={handleRun}
            running={running}
          />

          {selectedAnalysisId && (
            <>
              {comparisonLoading && (
                <Panel>
                  <div className="flex items-center justify-center gap-3 px-5 py-12 text-sm text-ink-muted">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
                    Loading scenarios…
                  </div>
                </Panel>
              )}
              {!comparisonLoading && comparisonError && (
                <Alert tone="error">{comparisonError}</Alert>
              )}
              {!comparisonLoading && !comparisonError && comparison.length > 0 && (
                <ScenarioComparisonTable
                  rows={comparison}
                  selectedCode={selectedCode}
                  onSelect={setSelectedCode}
                />
              )}
            </>
          )}

          {selectedAnalysisId && selectedCode && (
            <>
              {detailLoading && (
                <Panel>
                  <div className="flex items-center justify-center gap-3 px-5 py-12 text-sm text-ink-muted">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-line-strong border-t-accent" />
                    Loading scenario {selectedCode}…
                  </div>
                </Panel>
              )}
              {!detailLoading && detailError && <Alert tone="error">{detailError}</Alert>}
              {/* Render ONLY when the loaded lens matches the current selection — belt-and-suspenders
                  against a stale detail rendering (and being frozen) for the wrong lens. */}
              {!detailLoading && !detailError && detail && detail.code === selectedCode && (
                <ScenarioDetailPanel
                  detail={detail}
                  frozenAwardId={frozenAwardId}
                  onFreeze={() => {
                    setFreezeError(null);
                    setFreezeOpen(true);
                  }}
                />
              )}
            </>
          )}

          <FreezeAwardModal
            open={freezeOpen}
            onClose={() => setFreezeOpen(false)}
            onConfirm={handleFreezeConfirm}
            submitting={freezing}
            error={freezeError}
            scenarioCode={selectedCode ?? ""}
            scenarioLabel={detail?.code === selectedCode ? (detail?.label ?? "") : ""}
            suggestedCode={suggestedAwardCode}
          />
        </>
      )}
    </div>
  );
}
