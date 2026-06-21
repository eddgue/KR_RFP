import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type AlertTone = "error" | "success" | "info" | "warning";

export interface AlertProps {
  tone: AlertTone;
  children: ReactNode;
  className?: string;
}

// Inline message box — reuses the exact error treatment already used in the app
// (rounded-md border bg-red-50 …) and extends it to success / info / warning.
const tones: Record<AlertTone, string> = {
  error: "border-red-200 bg-red-50 text-red-700",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  info: "border-line bg-surface-subtle text-ink-muted",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
};

export function Alert({ tone, children, className }: AlertProps) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "rounded-md border px-3 py-2 text-sm",
        tones[tone],
        className,
      )}
    >
      {children}
    </div>
  );
}
