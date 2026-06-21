"use client";

import { useEffect, useState } from "react";
import { Button, FormField, Input, Modal } from "@/components/ui";
import { Alert } from "@/components/intake/Alert";
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

// Record a governed, append-only post-award adjustment LAYER: pick the cells to
// reprice, enter each new $/case, and capture the type / effective date / reason.
// The frozen baseline is never edited — this writes a new version on top
// (ADR-0014). The actual POST (+ its loading/error) is owned by the page.
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
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [adjustmentType, setAdjustmentType] = useState("");
  const [effectiveDate, setEffectiveDate] = useState(today());
  const [reason, setReason] = useState("");

  // Reset the form each time the dialog opens.
  useEffect(() => {
    if (!open) return;
    setDrafts({});
    setAdjustmentType("");
    setEffectiveDate(today());
    setReason("");
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
  const canSubmit =
    selectedKeys.length > 0 &&
    allPricesValid &&
    adjustmentType.trim() !== "" &&
    effectiveDate !== "" &&
    reason.trim() !== "" &&
    !submitting;

  const submit = () => {
    if (!canSubmit) return;
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
      reason: reason.trim(),
      changes,
    });
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Record adjustment"
      description={`Award ${awardCode}`}
      className="max-w-2xl"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" loading={submitting} disabled={!canSubmit} onClick={submit}>
            Record adjustment
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <p className="text-sm text-ink-muted">
          This writes an{" "}
          <span className="font-medium text-ink">append-only layer</span> on top of
          the frozen baseline — the baseline is never edited. Pick the cells to
          reprice and enter each new $/case.
        </p>

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-sm font-medium text-ink">Cells to reprice</span>
            <span className="text-xs text-ink-subtle">
              {selectedKeys.length} selected
            </span>
          </div>
          <div className="max-h-64 divide-y divide-line overflow-y-auto rounded-md border border-line">
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
                    className="h-4 w-4 shrink-0 accent-accent"
                  />
                  <label
                    htmlFor={`adj-cell-${key}`}
                    className="min-w-0 flex-1 cursor-pointer truncate"
                  >
                    <span className="text-ink">{l.dc}</span>
                    <span className="text-ink-subtle"> · </span>
                    <span className="text-ink-muted">
                      {l.lot} · {l.tf}
                    </span>
                    <span className="text-ink-subtle"> · </span>
                    <span className="font-medium text-ink">{l.supplier}</span>
                  </label>
                  <span className="w-20 shrink-0 text-right tabular-nums text-ink-muted">
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
                    <span className="w-28 shrink-0 text-right text-ink-subtle">—</span>
                  )}
                </div>
              );
            })}
          </div>
          <p className="mt-1 text-xs text-ink-subtle">
            Current effective $/case shown; enter the new price (&gt; 0).
          </p>
        </div>

        <FormField
          label="Adjustment type"
          htmlFor="adj-type"
          hint="A short label for the layer, e.g. MARKET_HIKE."
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
          hint="The business date the new prices take effect."
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

        <FormField
          label="Reason"
          htmlFor="adj-reason"
          hint="Why the adjustment was applied (recorded verbatim)."
          required
        >
          <textarea
            id="adj-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Trailing-4-week market reset…"
            disabled={submitting}
            rows={2}
            className="w-full rounded-md border border-line-strong bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:cursor-not-allowed disabled:bg-surface-muted disabled:opacity-70"
          />
        </FormField>

        {error && <Alert tone="error">{error}</Alert>}
      </div>
    </Modal>
  );
}
