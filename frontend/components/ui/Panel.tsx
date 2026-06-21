import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface PanelProps {
  className?: string;
  children: ReactNode;
}

// Card/Panel — the base surface for grouped content.
export function Panel({ className, children }: PanelProps) {
  return (
    <section
      className={cn(
        "rounded-panel border border-line bg-surface shadow-panel",
        className,
      )}
    >
      {children}
    </section>
  );
}

export interface PanelHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function PanelHeader({
  title,
  description,
  actions,
  className,
}: PanelHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-4 border-b border-line px-5 py-4",
        className,
      )}
    >
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        {description && (
          <p className="mt-0.5 text-sm text-ink-muted">{description}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
