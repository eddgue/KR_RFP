import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, invalid, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      className={cn(
        "h-9 w-full rounded-md border bg-white px-3 text-sm text-ink",
        "placeholder:text-ink-subtle",
        "focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent",
        "disabled:cursor-not-allowed disabled:bg-surface-muted disabled:opacity-70",
        invalid ? "border-red-400" : "border-line-strong",
        className,
      )}
      {...rest}
    />
  );
});
