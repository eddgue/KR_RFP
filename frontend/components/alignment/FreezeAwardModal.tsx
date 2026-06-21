"use client";

import { useEffect, useState } from "react";
import { Button, FormField, Input, Modal } from "@/components/ui";
import { Alert } from "@/components/intake/Alert";

// Freeze a chosen lens into a FROZEN award — a governed, immutable decision (the
// human asserts the award; ADR-0006). Collects the buyer's award code and fires
// `onConfirm`. The actual call (+ its loading/error) is owned by the page.
export function FreezeAwardModal({
  open,
  onClose,
  onConfirm,
  submitting,
  error,
  scenarioCode,
  scenarioLabel,
  suggestedCode,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (awardCode: string) => void;
  submitting: boolean;
  error: string | null;
  scenarioCode: string;
  scenarioLabel: string;
  suggestedCode: string;
}) {
  const [code, setCode] = useState(suggestedCode);

  // Reset to the suggested code each time the dialog opens.
  useEffect(() => {
    if (open) setCode(suggestedCode);
  }, [open, suggestedCode]);

  const trimmed = code.trim();

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Freeze award"
      description={`Lens ${scenarioCode} — ${scenarioLabel}`}
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            size="sm"
            loading={submitting}
            disabled={!trimmed || submitting}
            onClick={() => trimmed && onConfirm(trimmed)}
          >
            Freeze award
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <p className="text-sm text-ink-muted">
          Freezing promotes this lens to the official award. It is{" "}
          <span className="font-medium text-ink">immutable</span> — later changes
          are recorded as append-only post-award layers, never edits.
        </p>
        <FormField
          label="Award code"
          htmlFor="award-code"
          hint="Names the frozen award, e.g. AWD-2026-TOMATO-1."
          required
        >
          <Input
            id="award-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="AWD-2026-…"
            disabled={submitting}
            autoFocus
          />
        </FormField>
        {error && <Alert tone="error">{error}</Alert>}
      </div>
    </Modal>
  );
}
