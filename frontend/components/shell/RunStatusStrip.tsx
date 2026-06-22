import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type StatusTone = "live" | "frozen" | "sealed" | "idle";

export interface StatusCell {
  /** Short caps label, e.g. RUN STATE · ANALYSIS · AWARD · AUDIT. */
  label: string;
  value: ReactNode;
  tone?: StatusTone;
}

const dot: Record<StatusTone, string> = {
  live: "bg-success",
  frozen: "bg-success",
  sealed: "bg-sealed",
  idle: "bg-text-faint",
};

// The persistent four-cell run-status strip (Run · Analysis · Award · Audit).
// Each cell pairs a coloured dot with a caps label + a value; colour is always
// backed by text (WCAG AA — never hue alone).
export function RunStatusStrip({ cells }: { cells: StatusCell[] }) {
  return (
    <div className="flex w-full divide-x divide-border overflow-hidden rounded-card border border-border bg-surface-card shadow-card">
      {cells.map((c) => (
        <div key={c.label} className="flex min-w-0 flex-1 items-center gap-2.5 px-4 py-2.5">
          <span className={cn("h-2 w-2 shrink-0 rounded-full", dot[c.tone ?? "idle"])} aria-hidden />
          <div className="min-w-0 leading-tight">
            <p className="text-2xs font-bold uppercase tracking-wider text-text-subtle">{c.label}</p>
            <p className="truncate text-sm font-semibold text-text-strong">{c.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
