// Small display formatters shared across the intake UI.

// Human-readable byte size, e.g. 1536 -> "1.5 KB".
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

// Compact local timestamp from an ISO string; falls back to the raw value.
export function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// A monetary-ish number with 2 decimals, or em-dash for null.
export function formatPrice(value: number | null): string {
  if (value == null) return "—";
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// An integer count, or em-dash for null.
export function formatCount(value: number | null): string {
  if (value == null) return "—";
  return value.toLocaleString();
}

// A USD dollar amount, e.g. 1234567.5 -> "$1,234,568". Whole dollars by default
// (spend/savings totals are large); pass { cents: true } for 2-decimal precision.
export function formatMoney(
  value: number | null,
  opts?: { cents?: boolean },
): string {
  if (value == null) return "—";
  return value.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: opts?.cents ? 2 : 0,
    maximumFractionDigits: opts?.cents ? 2 : 0,
  });
}

// A fraction rendered as a percentage, e.g. 0.0524 -> "5.2%".
export function formatPercent(frac: number | null): string {
  if (frac == null) return "—";
  return frac.toLocaleString(undefined, {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}
