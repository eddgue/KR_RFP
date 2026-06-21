"use client";

import { useState } from "react";
import { ApiError, createRun } from "@/lib/api";
import type { RunDetail } from "@/lib/api";
import { Button, FormField, Input, Modal } from "@/components/ui";

export interface NewRunModalProps {
  open: boolean;
  onClose: () => void;
  // Called with the freshly created run so the parent can refresh / navigate.
  onCreated: (run: RunDetail) => void;
}

export function NewRunModal({ open, onClose, onCreated }: NewRunModalProps) {
  const [commodity, setCommodity] = useState("");
  const [label, setLabel] = useState("");
  const [rehearsal, setRehearsal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function reset() {
    setCommodity("");
    setLabel("");
    setRehearsal(false);
    setError(null);
    setSubmitting(false);
  }

  function handleClose() {
    if (submitting) return;
    reset();
    onClose();
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const run = await createRun({
        commodity: commodity.trim(),
        label: label.trim(),
        rehearsal,
      });
      reset();
      onCreated(run);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail || "Could not create the run."
          : "Unexpected error. Please try again.",
      );
      setSubmitting(false);
    }
  }

  const valid = commodity.trim().length > 0 && label.trim().length > 0;

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="New run"
      description="Start a sourcing run for a commodity."
      footer={
        <>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            form="new-run-form"
            loading={submitting}
            disabled={!valid}
          >
            Create run
          </Button>
        </>
      }
    >
      <form id="new-run-form" className="flex flex-col gap-4" onSubmit={onSubmit} noValidate>
        <FormField label="Commodity" htmlFor="commodity" required>
          <Input
            id="commodity"
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            placeholder="e.g. Corrugated Packaging"
            disabled={submitting}
            autoFocus
            required
          />
        </FormField>

        <FormField label="Label" htmlFor="label" required>
          <Input
            id="label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. FY26 H1 Rebid"
            disabled={submitting}
            required
          />
        </FormField>

        <label className="flex items-start gap-2.5 rounded-md border border-line bg-surface-subtle px-3 py-2.5">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 rounded border-line-strong text-accent focus:ring-2 focus:ring-accent/40"
            checked={rehearsal}
            onChange={(e) => setRehearsal(e.target.checked)}
            disabled={submitting}
          />
          <span className="text-sm">
            <span className="font-medium text-ink">Rehearsal run</span>
            <span className="block text-xs text-ink-muted">
              Practice run — kept separate from production sourcing.
            </span>
          </span>
        </label>

        {error && (
          <div
            role="alert"
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {error}
          </div>
        )}
      </form>
    </Modal>
  );
}
