"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  freezeAward,
  getRun,
  getScenarioComparison,
  getScenarioDetail,
  listAnalyses,
  nameVersion,
  runAnalysis,
} from "@/lib/api";
import type {
  AnalysisSummary,
  RunDetail,
  ScenarioComparisonRow,
  ScenarioDetail,
} from "@/lib/api";
import { Button, Panel, StatusChip } from "@/components/ui";
import { RunStatusStrip } from "@/components/shell/RunStatusStrip";
import { Alert } from "@/components/intake/Alert";
import { AnalysisRunsPanel } from "@/components/alignment/AnalysisRunsPanel";
import { ScenarioComparisonTable } from "@/components/alignment/ScenarioComparisonTable";
import { ScenarioDetailPanel } from "@/components/alignment/ScenarioDetailPanel";
import { FreezeAwardModal } from "@/components/alignment/FreezeAwardModal";
import { SaveVersionModal } from "@/components/alignment/SaveVersionModal";
import { ScenarioComparePanel } from "@/components/alignment/ScenarioComparePanel";

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

  // Save-version (savepoint) flow — a lightweight name on a sealed version (NOT a freeze).
  const [saveOpen, setSaveOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savingVersion, setSavingVersion] = useState<AnalysisSummary | null>(null);

  // Compare flow — the right-hand (saved) version to compare the working build against.
  const [compareRightId, setCompareRightId] = useState<string | null>(null);

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

  const handleSaveVersion = useCallback((a: AnalysisSummary) => {
    setSavingVersion(a);
    setSaveError(null);
    setSaveOpen(true);
  }, []);

  const handleSaveConfirm = useCallback(
    async (label: string) => {
      if (!savingVersion) return;
      setSaving(true);
      setSaveError(null);
      try {
        await nameVersion(slug, savingVersion.analysis_run_id, label);
        await loadAnalyses(savingVersion.analysis_run_id);
        setSaveOpen(false);
      } catch (err) {
        setSaveError(
          err instanceof ApiError ? err.detail : "Could not save the version.",
        );
      } finally {
        setSaving(false);
      }
    },
    [slug, savingVersion, loadAnalyses],
  );

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

  // The live seal is the most recently sealed (highest version); selecting any earlier
  // one is a read-only, historic view where governed actions are disabled.
  const liveAnalysis = useMemo(
    () =>
      analyses.length
        ? analyses.reduce((a, b) => (b.version > a.version ? b : a))
        : null,
    [analyses],
  );
  const selectedAnalysis = useMemo(
    () => analyses.find((a) => a.analysis_run_id === selectedAnalysisId) ?? null,
    [analyses, selectedAnalysisId],
  );
  const readOnly =
    !!selectedAnalysis && !!liveAnalysis && selectedAnalysis.version !== liveAnalysis.version;

  // Compare: the other versions you can hold the working build against, + the chosen one.
  const compareOptions = useMemo(
    () => analyses.filter((a) => a.analysis_run_id !== selectedAnalysisId),
    [analyses, selectedAnalysisId],
  );
  const compareRight = useMemo(
    () => compareOptions.find((a) => a.analysis_run_id === compareRightId) ?? null,
    [compareOptions, compareRightId],
  );

  const anyFrozen = Object.keys(frozen).length > 0;
  const selectedComparisonRow = useMemo(
    () => comparison.find((r) => r.code === selectedCode) ?? null,
    [comparison, selectedCode],
  );

  // Decision-header commodity chips (DCs · lots · suppliers · award cells · horizon),
  // computed from the selected lens detail so they reflect the lens actually shown.
  const headerChips = useMemo(() => {
    if (!detail || detail.code !== selectedCode) return [];
    const dcs = new Set(detail.cells.map((c) => c.dc));
    const lots = new Set(detail.cells.map((c) => c.lot));
    const suppliers = new Set<string>();
    for (const c of detail.cells) for (const s of c.suppliers) suppliers.add(s.name);
    const tfs = new Set(detail.cells.map((c) => c.tf));
    const chips: { label: string; value: string }[] = [
      { value: String(dcs.size), label: dcs.size === 1 ? "DC" : "DCs" },
      { value: String(lots.size), label: lots.size === 1 ? "lot" : "lots" },
      {
        value: String(suppliers.size),
        label: suppliers.size === 1 ? "supplier" : "suppliers",
      },
      {
        value: String(detail.cells.length),
        label: detail.cells.length === 1 ? "award cell" : "award cells",
      },
    ];
    if (tfs.size) chips.push({ value: "", label: [...tfs].join(" · ") });
    return chips;
  }, [detail, selectedCode]);

  return (
    <div className="flex flex-col gap-5">
      <nav className="text-sm text-text-muted">
        <Link href="/" className="hover:text-brand-primary">
          Runs
        </Link>
        <span className="px-1.5 text-text-subtle">/</span>
        <Link href={`/runs/${slug}`} className="hover:text-brand-primary">
          {run?.commodity ?? slug}
        </Link>
        <span className="px-1.5 text-text-subtle">/</span>
        <span className="font-semibold text-text-strong">Alignment</span>
      </nav>

      {runLoading && (
        <Panel>
          <div className="flex items-center justify-center gap-3 px-5 py-16 text-sm text-text-muted">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-border-hairline border-t-brand-primary" />
            Loading run…
          </div>
        </Panel>
      )}

      {!runLoading && runErr && (
        <Panel>
          <div className="px-5 py-16 text-center">
            <p className="text-sm font-semibold text-text-strong">
              {runErr.notFound ? "Run not found" : "Something went wrong"}
            </p>
            <p className="mt-1 text-sm text-text-muted">{runErr.message}</p>
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
          {/* persistent run-status strip */}
          <RunStatusStrip
            cells={[
              {
                label: "Run state",
                value: readOnly ? "Historic view" : "Live · Alignment",
                tone: readOnly ? "idle" : "live",
              },
              {
                label: "Analysis",
                value: selectedAnalysis
                  ? `Sealed · v${selectedAnalysis.version}`
                  : "Not sealed",
                tone: selectedAnalysis ? "sealed" : "idle",
              },
              {
                label: "Award",
                value: anyFrozen ? "Frozen" : "Not yet frozen",
                tone: anyFrozen ? "frozen" : "idle",
              },
              { label: "Audit", value: "Hash-chain current", tone: "live" },
            ]}
          />

          {/* read-only banner for a sealed, historic version */}
          {readOnly && liveAnalysis && (
            <div className="flex flex-wrap items-center gap-3 rounded-card border border-warning/40 bg-warning-bg px-4 py-3">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" className="shrink-0 text-warning" aria-hidden>
                <rect x="5" y="11" width="14" height="9" rx="2" />
                <path d="M8 11V8a4 4 0 0 1 8 0v3" />
              </svg>
              <span className="text-sm font-semibold text-text">
                You&rsquo;re viewing a sealed, read-only analysis (v
                {selectedAnalysis?.version}). Governed actions are disabled — switch to
                the live version to build or freeze.
              </span>
              <Button
                variant="secondary"
                size="sm"
                className="ml-auto"
                onClick={() => handleSelectAnalysis(liveAnalysis.analysis_run_id)}
              >
                View live version
              </Button>
            </div>
          )}

          {/* decision header */}
          <Panel className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <h1 className="font-display text-2xl font-extrabold tracking-tight text-text-strong">
                  Alignment workbench
                </h1>
                <p className="mt-1 text-sm text-text-muted">
                  {run.commodity} · {run.label}
                </p>
                {headerChips.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {headerChips.map((chip, i) => (
                      <span
                        key={`${chip.label}-${i}`}
                        className="rounded-control border border-border bg-surface-card px-2.5 py-1 text-xs font-semibold text-text-muted"
                      >
                        {chip.value && (
                          <b className="text-text-strong">{chip.value}</b>
                        )}{" "}
                        {chip.label}
                      </span>
                    ))}
                    {selectedCode && (
                      <span className="inline-flex items-center gap-1.5 rounded-control border border-border bg-surface-card px-2.5 py-1 text-xs font-semibold text-text-muted">
                        Lens
                        <StatusChip
                          tone={selectedComparisonRow?.is_recommended ? "green" : "sealed"}
                        >
                          {selectedCode}
                          {selectedComparisonRow?.is_recommended && " · REC"}
                        </StatusChip>
                      </span>
                    )}
                  </div>
                )}
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
            onSaveVersion={handleSaveVersion}
            running={running}
          />

          {/* compare the working build against a saved version (E-43, not a freeze) */}
          {compareOptions.length > 0 && selectedAnalysis && (
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-sm font-semibold text-text-strong">
                Compare v{selectedAnalysis.version} with
              </span>
              <select
                className="rounded-control border border-border bg-surface-card px-2.5 py-1.5 text-sm text-text focus:border-brand-primary"
                value={compareRight?.analysis_run_id ?? ""}
                onChange={(e) => setCompareRightId(e.target.value || null)}
              >
                <option value="">a saved version…</option>
                {compareOptions.map((a) => (
                  <option key={a.analysis_run_id} value={a.analysis_run_id}>
                    {a.label ? `v${a.version} · ${a.label}` : `v${a.version}`}
                  </option>
                ))}
              </select>
              {compareRight && (
                <Button variant="ghost" size="sm" onClick={() => setCompareRightId(null)}>
                  Clear
                </Button>
              )}
            </div>
          )}
          {compareRight && selectedAnalysis && (
            <ScenarioComparePanel slug={slug} left={selectedAnalysis} right={compareRight} />
          )}

          {selectedAnalysisId && (
            <>
              {comparisonLoading && (
                <Panel>
                  <div className="flex items-center justify-center gap-3 px-5 py-12 text-sm text-text-muted">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-border-hairline border-t-brand-primary" />
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
                  <div className="flex items-center justify-center gap-3 px-5 py-12 text-sm text-text-muted">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-border-hairline border-t-brand-primary" />
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
                  readOnly={readOnly}
                  capBreachCount={selectedComparisonRow?.cap_breach_count ?? null}
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

          <SaveVersionModal
            open={saveOpen}
            onClose={() => setSaveOpen(false)}
            onConfirm={handleSaveConfirm}
            submitting={saving}
            error={saveError}
            version={savingVersion?.version ?? null}
            currentLabel={savingVersion?.label ?? null}
          />
        </>
      )}
    </div>
  );
}
