"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getStrategy, updateStrategy } from "@/lib/api";
import type { Strategy } from "@/lib/api";
import { Button, Panel } from "@/components/ui";

// The minimal A1 strategy slice: review + tune the engine config the NEXT analysis
// runs under (the named weight preset + the four safeties). Persists onto the cycle.

const PRESETS: { value: string; label: string }[] = [
  { value: "balanced", label: "Balanced" },
  { value: "price_focus", label: "Price focus" },
  { value: "coverage_focus", label: "Coverage focus" },
  { value: "risk_averse", label: "Risk averse" },
  { value: "custom", label: "Custom" },
];

const WEIGHTS: { key: keyof Strategy; label: string }[] = [
  { key: "weight_price", label: "Price" },
  { key: "weight_coverage", label: "Coverage" },
  { key: "weight_historical", label: "Historical" },
  { key: "weight_zrisk", label: "Z-risk" },
  { key: "weight_continuity", label: "Continuity" },
];

const pct = (n: number) => `${Math.round(n * 100)}%`;

const fieldCls =
  "w-full rounded-control border border-border bg-surface-card px-2.5 py-1.5 text-sm text-text focus:border-brand-primary";

function NumField({
  label,
  value,
  step,
  onChange,
}: {
  label: string;
  value: string;
  step: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-2xs font-bold uppercase tracking-wide text-text-muted">
        {label}
      </span>
      <input
        type="number"
        className={`${fieldCls} tabular-nums`}
        value={value}
        step={step}
        min="0"
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

export function StrategyPanel({ slug }: { slug: string }) {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [preset, setPreset] = useState("balanced");
  const [premium, setPremium] = useState("0.12");
  const [coverage, setCoverage] = useState("0.80");
  const [conc, setConc] = useState("0.40");
  const [maxSup, setMaxSup] = useState("2");

  const hydrate = useCallback((s: Strategy) => {
    setStrategy(s);
    setPreset(s.weight_preset);
    setPremium(String(s.premium_ceiling));
    setCoverage(String(s.coverage_floor));
    setConc(String(s.conc_thresh));
    setMaxSup(String(s.max_sup_dc));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      hydrate(await getStrategy(slug));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail || "Could not load strategy." : "Could not load strategy.",
      );
    } finally {
      setLoading(false);
    }
  }, [slug, hydrate]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = useCallback(async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await updateStrategy(slug, {
        weight_preset: preset,
        premium_ceiling: Number(premium),
        coverage_floor: Number(coverage),
        conc_thresh: Number(conc),
        max_sup_dc: Number(maxSup),
      });
      hydrate(updated);
      setSaved(true);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail || "Could not save strategy." : "Could not save strategy.",
      );
    } finally {
      setSaving(false);
    }
  }, [slug, preset, premium, coverage, conc, maxSup, hydrate]);

  const dirty =
    !!strategy &&
    (preset !== strategy.weight_preset ||
      Number(premium) !== strategy.premium_ceiling ||
      Number(coverage) !== strategy.coverage_floor ||
      Number(conc) !== strategy.conc_thresh ||
      Number(maxSup) !== strategy.max_sup_dc);

  return (
    <Panel className="overflow-hidden">
      <div className="flex items-center justify-between gap-2 border-b border-border-hairline px-4 py-3">
        <h3 className="text-sm font-bold text-text-strong">Strategy</h3>
        <span className="text-2xs text-text-subtle">Used by the next analysis</span>
      </div>

      {loading ? (
        <p className="px-4 py-6 text-center text-xs text-text-subtle">Loading…</p>
      ) : (
        <div className="flex flex-col gap-3 px-4 py-3.5">
          <label className="block">
            <span className="mb-1 block text-2xs font-bold uppercase tracking-wide text-text-muted">
              Weight preset
            </span>
            <select className={fieldCls} value={preset} onChange={(e) => setPreset(e.target.value)}>
              {PRESETS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>

          {strategy && (
            <div className="rounded-control border border-border-hairline bg-surface-subtle px-2.5 py-2">
              <p className="mb-1 text-2xs font-bold uppercase tracking-wide text-text-subtle">
                Scoring weights
              </p>
              <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                {WEIGHTS.map((w) => (
                  <span key={w.key} className="text-xs text-text-muted">
                    {w.label}{" "}
                    <strong className="tabular-nums text-text-strong">
                      {pct(strategy[w.key] as number)}
                    </strong>
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2.5">
            <NumField label="Premium ceiling" value={premium} step="0.01" onChange={setPremium} />
            <NumField label="Coverage floor" value={coverage} step="0.01" onChange={setCoverage} />
            <NumField label="Concentration" value={conc} step="0.01" onChange={setConc} />
            <NumField label="Max suppliers/DC" value={maxSup} step="1" onChange={setMaxSup} />
          </div>

          {error && <p className="text-xs text-danger">{error}</p>}
          <div className="flex items-center justify-between gap-2">
            <span className="text-2xs text-text-subtle">
              {dirty ? "Unsaved changes" : saved ? "Saved ✓" : "Up to date"}
            </span>
            <Button size="sm" loading={saving} disabled={!dirty} onClick={() => void save()}>
              Save strategy
            </Button>
          </div>
        </div>
      )}
    </Panel>
  );
}
