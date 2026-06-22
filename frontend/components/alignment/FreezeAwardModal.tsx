"use client";

import { useEffect, useState } from "react";
import { AssertModal, FormField, Input, StatusChip } from "@/components/ui";
import { useAuth } from "@/components/auth/AuthProvider";

// Freeze a chosen lens into a FROZEN award — the governed, immutable decision (the
// human asserts the award; ADR-0006). Built on the shared AssertModal pattern:
// summary of the scenario/lens being frozen → named assertion → confirm. Collects the
// buyer's award code; on confirm fires `onConfirm(awardCode)` with the SAME arg the
// page's freezeAward call uses. The POST (+ its loading/error) is owned by the page.
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
  const { user } = useAuth();
  const [code, setCode] = useState(suggestedCode);

  // Reset to the suggested code each time the dialog opens.
  useEffect(() => {
    if (open) setCode(suggestedCode);
  }, [open, suggestedCode]);

  const trimmed = code.trim();

  return (
    <AssertModal
      open={open}
      onClose={onClose}
      title="Freeze award"
      description="Governed action — promotes this lens to the official, immutable award."
      eventType="FROZEN"
      actorName={user?.username ?? "you"}
      confirmLabel="Freeze award"
      loading={submitting}
      error={trimmed ? error : (error ?? "Enter an award code to freeze.")}
      onConfirm={() => {
        if (trimmed) onConfirm(trimmed);
      }}
      summary={
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <StatusChip tone="sealed">Lens {scenarioCode}</StatusChip>
            <span className="font-semibold text-text-strong">{scenarioLabel}</span>
          </div>
          <p className="text-sm text-text-muted">
            Freezing promotes this lens to the official award. It is{" "}
            <span className="font-semibold text-text-strong">immutable</span> — later
            changes are recorded as append-only post-award layers, never edits.
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
        </div>
      }
    />
  );
}
