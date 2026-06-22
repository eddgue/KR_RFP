"use client";

import { useEffect, useState } from "react";
import { Modal, Button } from "@/components/ui";

// A LIGHTWEIGHT savepoint — name the current sealed alignment version so it can be found and
// compared later. Deliberately NOT the freeze flow: no governance copy, no audit event, no award.
export function SaveVersionModal({
  open,
  onClose,
  onConfirm,
  submitting,
  error,
  version,
  currentLabel,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (label: string) => void | Promise<void>;
  submitting: boolean;
  error: string | null;
  version: number | null;
  currentLabel: string | null;
}) {
  const [label, setLabel] = useState("");

  useEffect(() => {
    if (open) setLabel(currentLabel ?? "");
  }, [open, currentLabel]);

  const canSave = label.trim().length > 0 && !submitting;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Save this version"
      description={
        version
          ? `Name version v${version} so you can find it later and compare against it.`
          : undefined
      }
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            size="sm"
            loading={submitting}
            disabled={!canSave}
            onClick={() => void onConfirm(label.trim())}
          >
            Save version
          </Button>
        </>
      }
    >
      <label className="block">
        <span className="mb-1 block text-2xs font-bold uppercase tracking-wide text-text-muted">
          Version name
        </span>
        <input
          type="text"
          value={label}
          maxLength={120}
          autoFocus
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && canSave) void onConfirm(label.trim());
          }}
          placeholder="e.g. Balanced baseline"
          className="w-full rounded-control border border-border bg-surface-card px-3 py-2 text-sm text-text placeholder:text-text-faint focus:border-brand-primary"
        />
      </label>
      <p className="mt-2 text-xs text-text-subtle">
        A savepoint records the current sealed build under a name. It writes no audit event and does
        not freeze the award — freeze stays the separate, governed step.
      </p>
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
    </Modal>
  );
}
