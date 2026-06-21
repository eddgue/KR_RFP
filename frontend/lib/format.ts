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
