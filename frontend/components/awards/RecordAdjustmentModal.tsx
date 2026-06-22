"use client";

import { useEffect, useState } from "react";
import { AssertModal, FormField, Input } from "@/components/ui";
import { useAuth } from "@/components/auth/AuthProvider";
import { formatPrice } from "@/lib/format";
import type {
  AdjustmentLineChange,
  AwardLineView,
  RecordAdjustmentBody,
} from "@/lib/api";

// A few common layer types as suggestions (free text — reasons/types are
// data-derived, not a fixed enum, per D28).
const TYPE_SUGGESTIONS = [
  "MARKET_HIKE",
  "MARKET_DROP",
  "TOLERANCE_BAND",
  "CONTRACT_AMENDMENT",
];

const cellKey = (l: AwardLineView) =>
  `${l.dc_id}|${l.lot_id}|${l.tf_id}|${l.supplier_id}`;

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function isValidPrice(raw: string | undefined): boolean {
  if (raw == null || raw.trim() === "") return false;
  const v = Number(raw);
  return Number.isFinite(v) && v > 0;
}

// Record a governed, append-only post-award adjustment LAYER, built on the shared
// AssertModal pattern: summary (cells to reprice + type + effective date) → rationale
// → named assertion → confirm. The frozen baseline is never edited — this writes a new
// version on top (ADR-0014). The AssertModal rationale IS the layer's reason. The
// actual POST (+ its loading/error) is owned by the page; `onConfirm` fires with the
// same RecordAdjustmentBody payload as before.
//
// `drafts` is the single source of truth for the cell grid: a cell is selected iff
// its key is present, and the value is the new-price string being typed.
export function RecordAdjustmentModal({
  open,
  onClose,
  onConfirm,
  submitting,
  error,
  awardCode,
  lines,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (body: RecordAdjustmentBody) => void;
  submitting: boolean;
  error: string | null;
  awardCode: string;
  lines: AwardLineView[];
}) {
  const { user } = useAuth();
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [adjustmentType, setAdjustmentType] = useState("");
  const [effectiveDate, setEffectiveDate] = useState(today());

  // Reset the form each time the dialog opens.
  useEffect(() => {
    if (!open) return;
    setDrafts({});
    setAdjustmentType("");
    setEffectiveDate(today());
  }, [open]);

  const toggle = (line: AwardLineView) => {
    const key = cellKey(line);
    setDrafts((prev) => {
      if (key in prev) {
        const next = { ...prev };
        delete next[key];
        return next;
      }
      // Seed the input with the cell's current effective price to edit from.
      return { ...prev, [key]: line.effective_price.toFixed(2) };
    });
  };

  const setPrice = (key: string, value: string) =>
    setDrafts((prev) => ({ ...prev, [key]: value }));

  const selectedKeys = Object.keys(drafts);
  const allPricesValid = selectedKeys.every((k) => isValidPrice(drafts[k]));
  // Gate the local form fields (cells + type + date). The named assertion + rationale
  // (reason) are enforced by AssertModal.
  const formReady =
    selectedKeys.length > 0 &&
    allPricesValid &&
    adjustmentType.trim() !== "" &&
    effectiveDate !== "";

  const submit = (rationale: string) => {
    if (!formReady) return;
    const changes: AdjustmentLineChange[] = lines
      .filter((l) => cellKey(l) in drafts)
      .map((l) => ({
        dc_id: l.dc_id,
        lot_id: l.lot_id,
        tf_id: l.tf_id,
        supplier_id: l.supplier_id,
        new_price: Number(drafts[cellKey(l)]),
      }));
    onConfirm({
      adjustment_type: adjustmentType.trim(),
      effective_date: effectiveDate,
      reason: rationale,
      changes,
    });
  };

  // Surface a gentle prompt if the human asserts before the form is complete.
  const effectiveError =
    error ?? (!formReady && selectedKeys.length === 0
      ? "Select at least one cell to reprice."
      : !formReady
        ? "Complete the new price, type and effective date."
        : null);

  return (
    <AssertModal
      open={open}
      onClose={onClose}
      title="Record adjustment"
      description={`Append a new versioned layer over ${awardCode} — the baseline never changes.`}
      eventType="ADJUSTMENT"
      actorName={user?.username ?? "you"}
      withRationale
      rationaleLabel="Reason"
      rationaleRequired
      confirmLabel="Record adjustment"
      loading={submitting}
      error={effectiveError}
      onConfirm={submit}
      summary={
        <div className="space-y-4">
          <p className="text-sm text-text-muted">
            This writes an{" "}
            <span className="font-semibold text-text-strong">append-only layer</span>{" "}
            on top of the frozen baseline. Pick the cells to reprice and enter each new
            $/case.
          </p>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-2xs font-bold uppercase tracking-wide text-text-muted">
                Cells to reprice
              </span>
              <span className="text-2xs text-text-subtle">
                {selectedKeys.length} selected
              </span>
            </div>
            <div className="max-h-56 divide-y divide-border-hairline overflow-y-auto rounded-control border border-border bg-surface-card">
              {lines.map((l) => {
                const key = cellKey(l);
                const checked = key in drafts;
                return (
                  <div key={key} className="flex items-center gap-3 px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      id={`adj-cell-${key}`}
                      checked={checked}
                      onChange={() => toggle(l)}
                      disabled={submitting}
                      className="h-4 w-4 shrink-0 accent-brand-primary"
                    />
                    <label
                      htmlFor={`adj-cell-${key}`}
                      className="min-w-0 flex-1 cursor-pointer truncate"
                    >
                      <span className="text-text-strong">{l.dc}</span>
                      <span className="text-text-subtle"> · </span>
                      <span className="text-text-muted">
                        {l.lot} · {l.tf}
                      </span>
                      <span className="text-text-subtle"> · </span>
                      <span className="font-medium text-text">{l.supplier}</span>
                    </label>
                    <span className="w-20 shrink-0 text-right tabular-nums text-text-faint">
                      {formatPrice(l.effective_price)}
                    </span>
                    {checked ? (
                      <Input
                        type="number"
                        inputMode="decimal"
                        step="0.01"
                        min="0"
                        aria-label={`New price for ${l.supplier}`}
                        value={drafts[key]}
                        onChange={(e) => setPrice(key, e.target.value)}
                        invalid={!isValidPrice(drafts[key])}
                        disabled={submitting}
                        className="h-8 w-28 shrink-0"
                      />
                    ) : (
                      <span className="w-28 shrink-0 text-right text-text-subtle">—</span>
                    )}
                  </div>
                );
              })}
            </div>
            <p className="mt-1 text-2xs text-text-subtle">
              Current effective $/case shown; enter the new price (&gt; 0).
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField
              label="Adjustment type"
              htmlFor="adj-type"
              hint="A short label for the layer."
              required
            >
              <Input
                id="adj-type"
                list="adj-type-options"
                value={adjustmentType}
                onChange={(e) => setAdjustmentType(e.target.value)}
                placeholder="MARKET_HIKE"
                disabled={submitting}
              />
              <datalist id="adj-type-options">
                {TYPE_SUGGESTIONS.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
            </FormField>

            <FormField
              label="Effective date"
              htmlFor="adj-date"
              hint="When the new prices take effect."
              required
            >
              <Input
                id="adj-date"
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                disabled={submitting}
              />
            </FormField>
          </div>
        </div>
      }
    />
  );
}
