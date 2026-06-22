"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";
import { StatusChip } from "./StatusChip";

export interface AssertModalProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  /** What this governed action will do — summary content/rows. */
  summary?: ReactNode;
  /** Cautions to surface before the assertion (irreversible / gated). */
  cautions?: ReactNode;
  /** The audit event that WILL be written (e.g. FROZEN, CLOSED). */
  eventType: string;
  /** Current actor's display name, woven into the named assertion. */
  actorName: string;
  /** Show a free-text rationale field (decision capture, E-40). */
  withRationale?: boolean;
  rationaleLabel?: string;
  rationaleRequired?: boolean;
  confirmLabel?: string;
  /** Render the confirm as a destructive action. */
  destructive?: boolean;
  onConfirm: (rationale: string) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
}

// The single governed-action pattern: summary -> cautions -> (optional
// rationale) -> NAMED assertion -> confirm. Confirm is disabled until the
// human asserts; the audit event that will be written is shown up front.
export function AssertModal({
  open,
  onClose,
  title,
  description,
  summary,
  cautions,
  eventType,
  actorName,
  withRationale = false,
  rationaleLabel = "Rationale",
  rationaleRequired = false,
  confirmLabel = "Confirm",
  destructive = false,
  onConfirm,
  loading = false,
  error = null,
}: AssertModalProps) {
  const [asserted, setAsserted] = useState(false);
  const [rationale, setRationale] = useState("");

  // Reset the assertion each time the modal opens.
  useEffect(() => {
    if (open) {
      setAsserted(false);
      setRationale("");
    }
  }, [open]);

  const rationaleOk = !withRationale || !rationaleRequired || rationale.trim().length > 0;
  const canConfirm = asserted && rationaleOk && !loading;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant={destructive ? "danger" : "primary"}
            size="sm"
            loading={loading}
            disabled={!canConfirm}
            onClick={() => void onConfirm(rationale.trim())}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {summary && (
          <div className="rounded-card border border-border bg-surface-subtle p-3 text-sm text-text">
            {summary}
          </div>
        )}
        {cautions && (
          <div className="rounded-card border border-warning/40 bg-warning-bg p-3 text-sm text-text">
            {cautions}
          </div>
        )}
        {withRationale && (
          <label className="block">
            <span className="mb-1 block text-2xs font-bold uppercase tracking-wide text-text-muted">
              {rationaleLabel}
              {rationaleRequired && " *"}
            </span>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              rows={3}
              className="w-full rounded-control border border-border bg-surface-card px-3 py-2 text-sm text-text placeholder:text-text-faint focus:border-brand-primary"
              placeholder="Why this decision (recorded in the audit trail)…"
            />
          </label>
        )}
        <label className="flex items-start gap-2.5 rounded-card border border-border bg-surface-subtle p-3 text-sm text-text">
          <input
            type="checkbox"
            checked={asserted}
            onChange={(e) => setAsserted(e.target.checked)}
            className="mt-0.5 h-4 w-4 accent-brand-primary"
          />
          <span>
            I, <strong className="text-text-strong">{actorName}</strong>, assert this decision. Recorded
            against my name in the audit trail.
          </span>
        </label>
        <div className="flex items-center gap-2 text-2xs text-text-muted">
          <span>Audit event:</span>
          <StatusChip tone="sealed">{eventType}</StatusChip>
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
      </div>
    </Modal>
  );
}
