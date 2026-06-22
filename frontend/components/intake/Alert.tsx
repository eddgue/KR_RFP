import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type AlertTone = "error" | "success" | "info" | "warning";

export interface AlertProps {
  tone: AlertTone;
  children: ReactNode;
  className?: string;
}

// Inline message box — locked v2 tokens. Colour is always backed by text.
const tones: Record<AlertTone, string> = {
  error: "border-danger/30 bg-danger-bg text-danger",
  success: "border-success/30 bg-success-bg text-success",
  info: "border-border bg-surface-subtle text-text-muted",
  warning: "border-warning/30 bg-warning-bg text-warning",
};

export function Alert({ tone, children, className }: AlertProps) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "rounded-control border px-3 py-2 text-sm",
        tones[tone],
        className,
      )}
    >
      {children}
    </div>
  );
}
