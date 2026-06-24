"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { riskConfig, statusConfig } from "@/lib/risk";
import type { RiskTier } from "@/lib/types";

// Re-export page layout primitives so all pages can import from one module.
export { PageTransition, PageHeader } from "@/components/layout/page";

export function RiskBadge({ tier, score, className }: { tier: RiskTier; score?: number; className?: string }) {
  const c = riskConfig[tier] || {
    label: tier || "Unknown",
    chip: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        c.chip,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", c.dot)} />
      {c.label}
      {typeof score === "number" && <span className="nums opacity-70">· {score}%</span>}
    </span>
  );
}

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const c = statusConfig[status] ?? { label: status, chip: "bg-muted text-muted-foreground border-border", dot: "bg-muted-foreground" };
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium", c.chip, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", c.dot)} />
      {c.label}
    </span>
  );
}

export function GlassPanel({ children, className, strong }: { children: React.ReactNode; className?: string; strong?: boolean }) {
  return <div className={cn(strong ? "glass-strong" : "glass", "rounded-2xl", className)}>{children}</div>;
}

export function GradientBorderPanel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("border-gradient rounded-2xl", className)}>{children}</div>;
}

export function SectionHeading({ eyebrow, title, description, className, action }: { eyebrow?: string; title: string; description?: string; className?: string; action?: React.ReactNode }) {
  return (
    <div className={cn("flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div>
        {eyebrow && <div className="mb-1.5 text-[11px] font-medium uppercase tracking-[0.2em] text-brand">{eyebrow}</div>}
        <h2 className="font-heading text-2xl font-medium tracking-tight text-balance">{title}</h2>
        {description && <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground text-pretty">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function EmptyState({ icon, title, description, action, className }: { icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card/40 px-6 py-16 text-center", className)}>
      {icon && <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">{icon}</div>}
      <h3 className="font-heading text-lg font-medium">{title}</h3>
      {description && <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Sparkline({ data, color = "var(--brand)", className, width = 120, height = 36 }: { data: number[]; color?: string; className?: string; width?: number; height?: number }) {
  if (data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1 || 1);
  const pts = data.map((d, i) => `${i * step},${height - ((d - min) / range) * height}`);
  const path = `M ${pts.join(" L ")}`;
  const area = `${path} L ${width},${height} L 0,${height} Z`;
  const id = React.useId();
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path d={path} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function LiveDot({ className, color = "var(--risk-low)" }: { className?: string; color?: string }) {
  return (
    <span className={cn("relative inline-flex h-2 w-2", className)}>
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60" style={{ background: color }} />
      <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: color }} />
    </span>
  );
}
