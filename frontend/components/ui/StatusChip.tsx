import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "accent" | "amber" | "green" | "slate";

export interface StatusChipProps {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}

const tones: Record<Tone, string> = {
  neutral: "bg-surface-muted text-ink-muted ring-line-strong",
  accent: "bg-accent-soft text-accent ring-accent/25",
  amber: "bg-amber-50 text-amber-700 ring-amber-200",
  green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  slate: "bg-slate-100 text-slate-600 ring-slate-300",
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
