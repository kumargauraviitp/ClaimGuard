// ClaimGuard formatting helpers (INR-first, locale-aware)

export function inr(value: number | undefined | null, opts?: { compact?: boolean; decimals?: number }): string {
  if (value == null || !Number.isFinite(value)) return "₹0";
  if (opts?.compact) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value);
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: opts?.decimals ?? 0,
  }).format(value);
}

export function compactNum(value: number | undefined | null): string {
  if (value == null || !Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function num(value: number): string {
  return new Intl.NumberFormat("en-IN").format(value);
}

export function pct(value: number | undefined | null, decimals = 1): string {
  if (value == null || !Number.isFinite(value)) return "0.0%";
  return `${(value * 100).toFixed(decimals)}%`;
}

export function pctRaw(value: number | undefined | null, decimals = 0): string {
  if (value == null || !Number.isFinite(value)) return "0%";
  return `${value.toFixed(decimals)}%`;
}

export function relativeTime(iso: string): string {
  const date = new Date(iso);
  const diffMs = date.getTime() - Date.now();
  const diffMin = Math.round(diffMs / 60000);
  const abs = Math.abs(diffMin);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  if (abs < 60) return rtf.format(Math.round(diffMin), "minute");
  if (abs < 60 * 24) return rtf.format(Math.round(diffMin / 60), "hour");
  if (abs < 60 * 24 * 30) return rtf.format(Math.round(diffMin / 60 / 24), "day");
  if (abs < 60 * 24 * 365) return rtf.format(Math.round(diffMin / 60 / 24 / 30), "month");
  return rtf.format(Math.round(diffMin / 60 / 24 / 365), "year");
}

export function fmtDate(iso: string, opts?: Intl.DateTimeFormatOptions): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", opts ?? { day: "2-digit", month: "short", year: "numeric" });
}

export function fmtDateTime(iso: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function hoursBetween(a: string, b: string): number {
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / 3600000);
}
