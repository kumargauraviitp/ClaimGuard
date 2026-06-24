"use client";

import * as React from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";
import { riskConfig, tierColorVar } from "@/lib/risk";
import type { RiskTier } from "@/lib/types";

type Size = "sm" | "md" | "lg" | "xl";

const sizes: Record<Size, { box: number; stroke: number; label: string }> = {
  sm: { box: 96, stroke: 8, label: "text-sm" },
  md: { box: 140, stroke: 11, label: "text-2xl" },
  lg: { box: 188, stroke: 14, label: "text-4xl" },
  xl: { box: 248, stroke: 18, label: "text-6xl" },
};

export function RiskGauge({
  value,
  tier,
  size = "lg",
  label,
  sublabel,
  showHalo = true,
  className,
}: {
  value: number;
  tier: RiskTier;
  size?: Size;
  label?: string;
  sublabel?: string;
  showHalo?: boolean;
  className?: string;
}) {
  const s = sizes[size];
  const r = (s.box - s.stroke) / 2;
  const cx = s.box / 2;
  const startAngle = 135;
  const sweep = 270;
  const clamped = Math.max(0, Math.min(100, value));
  const fraction = clamped / 100;
  const valueAngle = startAngle + sweep * fraction;

  const polar = (angle: number, radius: number) => {
    const rad = (angle * Math.PI) / 180;
    // Round to 2 decimals — SVG needs no more, and this guarantees the server
    // and browser render identical strings (avoids SSR hydration mismatch from
    // last-digit float differences between Node and V8).
    return {
      x: Math.round((cx + radius * Math.cos(rad)) * 100) / 100,
      y: Math.round((cx + radius * Math.sin(rad)) * 100) / 100,
    };
  };

  const describeArc = (fromAngle: number, toAngle: number, radius: number) => {
    const start = polar(fromAngle, radius);
    const end = polar(toAngle, radius);
    const large = toAngle - fromAngle > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${large} 1 ${end.x} ${end.y}`;
  };

  const trackPath = describeArc(startAngle, startAngle + sweep, r);
  const color = tierColorVar(tier);

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: s.box, height: s.box }}>
      {showHalo && (
        <div
          className="conic-sweep absolute inset-0 rounded-full opacity-30 blur-md"
          style={{
            maskImage: "radial-gradient(closest-side, transparent 62%, #000 64%, #000 100%)",
            WebkitMaskImage: "radial-gradient(closest-side, transparent 62%, #000 64%, #000 100%)",
          }}
          aria-hidden
        />
      )}
      <svg width={s.box} height={s.box} viewBox={`0 0 ${s.box} ${s.box}`} className="relative">
        <defs>
          <linearGradient id={`g-${tier}-${size}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.55" />
            <stop offset="100%" stopColor={color} stopOpacity="1" />
          </linearGradient>
        </defs>
        <path d={trackPath} fill="none" stroke="var(--muted)" strokeWidth={s.stroke} strokeLinecap="round" opacity={0.55} />
        <motion.path
          d={trackPath}
          pathLength={1}
          fill="none"
          stroke={`url(#g-${tier}-${size})`}
          strokeWidth={s.stroke}
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: fraction }}
          transition={{ duration: 1.3, ease: [0.22, 1, 0.36, 1] }}
        />
        {Array.from({ length: 28 }).map((_, i) => {
          const a = startAngle + (sweep / 27) * i;
          const outer = polar(a, r + s.stroke / 2 + 3);
          const inner = polar(a, r + s.stroke / 2 + 1);
          const filled = a <= valueAngle;
          return (
            <line
              key={i}
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              stroke={filled ? color : "var(--border)"}
              strokeWidth={1.5}
              strokeLinecap="round"
              opacity={filled ? 0.9 : 0.4}
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("font-heading font-medium nums", s.label)} style={{ color: "var(--foreground)" }}>
          {Math.round(clamped)}
          <span className="text-muted-foreground text-2xl">%</span>
        </span>
        {label && <span className="mt-0.5 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{label}</span>}
        {sublabel && (
          <span className={cn("mt-1 text-xs font-medium", riskConfig[tier]?.text || "text-muted-foreground")}>{sublabel}</span>
        )}
      </div>
    </div>
  );
}
