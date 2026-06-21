import type { ReactNode, ThHTMLAttributes, TdHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

// Compact, data-first table primitives.

export function Table({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className="w-full overflow-x-auto">
      <table className={cn("w-full border-collapse text-sm", className)}>
        {children}
      </table>
    </div>
  );
}

export function THead({ children }: { children: ReactNode }) {
  return <thead className="bg-surface-subtle">{children}</thead>;
}

export function TBody({ children }: { children: ReactNode }) {
  return <tbody className="divide-y divide-line">{children}</tbody>;
}

export function TR({
  children,
  className,
  onClick,
  ...rest
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
} & React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(onClick && "cursor-pointer hover:bg-surface-subtle", className)}
      onClick={onClick}
      {...rest}
    >
      {children}
    </tr>
  );
}

export function TH({
  children,
  className,
  ...rest
}: { children: ReactNode } & ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      scope="col"
      className={cn(
        "border-b border-line px-4 py-2.5 text-left text-2xs font-semibold uppercase tracking-wide text-ink-subtle",
        className,
      )}
      {...rest}
    >
      {children}
    </th>
  );
}

export function TD({
  children,
  className,
  ...rest
}: { children: ReactNode } & TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn("px-4 py-2.5 align-middle text-ink", className)} {...rest}>
      {children}
    </td>
  );
}
