import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type StepState = "done" | "current" | "todo";

export interface StepHeaderProps {
  // 1-based step number, shown when the step isn't yet complete.
  step: number;
  title: string;
  description?: ReactNode;
  state: StepState;
  // Right-aligned slot — typically a completion StatusChip and/or an action.
  actions?: ReactNode;
}

// Shared header for the sequential intake STEP cards: a numbered/checkmark
// badge, the title + description, and a right-aligned completion/action slot.
export function StepHeader({
  step,
  title,
  description,
  state,
  actions,
}: StepHeaderProps) {
  return (
    <div className="flex items-center gap-3.5 border-b border-border-hairline px-[18px] py-4">
      <span
        className={cn(
          "flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full border-2 text-sm font-extrabold tabular-nums",
          state === "done" && "border-success bg-success text-white",
          state === "current" &&
            "border-brand-primary bg-sealed-bg text-brand-primary",
          state === "todo" && "border-border bg-surface-card text-text-faint",
        )}
        aria-hidden
      >
        {state === "done" ? "✓" : step}
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="text-[15px] font-bold text-text-strong">
          {step} · {title}
        </h2>
        {description && (
          <p className="text-xs text-text-muted">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 items-center gap-2">{actions}</div>
      )}
    </div>
  );
}
