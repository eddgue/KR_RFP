import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Tone =
  | "neutral"
  | "accent"
  | "amber"
  | "green"
  | "slate"
  // governed status language (locked v2 — always colour + text, never hue alone)
  | "frozen"
  | "sealed"
  | "modeled"
  | "gated";

export interface StatusChipProps {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}

const tones: Record<Tone, string> = {
  neutral: "bg-surface-muted text-text-muted ring-border",
  accent: "bg-accent-soft text-accent ring-accent/25",
  amber: "bg-warning-bg text-warning ring-warning/30",
  green: "bg-success-bg text-success ring-success/30",
  slate: "bg-slate-100 text-slate-600 ring-slate-300",
  frozen: "bg-success-bg text-success ring-success/30",
  sealed: "bg-sealed-bg text-sealed ring-sealed/25",
  modeled: "bg-warning-bg text-warning ring-warning/30",
  gated: "bg-danger-bg text-danger ring-danger/30",
};

export function StatusChip({
  children,
  tone = "neutral",
  className,
}: StatusChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-medium uppercase tracking-wide ring-1 ring-inset",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

// Map a free-form run "stage" string to a sensible chip tone.
export function stageTone(stage: string): Tone {
  const s = stage.toLowerCase();
  if (/(done|complete|award|closed)/.test(s)) return "green";
  if (/(wait|review|action|hold|blocked)/.test(s)) return "amber";
  if (/(active|progress|doing|open|round)/.test(s)) return "accent";
  return "slate";
}
