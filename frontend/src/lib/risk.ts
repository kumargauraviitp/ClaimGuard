import type { RiskTier } from "@/lib/types";

export const riskConfig: Record<
  RiskTier,
  { label: string; token: string; text: string; bg: string; ring: string; dot: string; chip: string }
> = {
  high: {
    label: "High Risk",
    token: "var(--risk-high)",
    text: "text-risk-high",
    bg: "bg-risk-high/12",
    ring: "ring-risk-high/30",
    dot: "bg-risk-high",
    chip: "bg-risk-high/12 text-risk-high border-risk-high/25",
  },
  critical: {
    label: "Critical",
    token: "var(--risk-high)", // Using high tokens for critical
    text: "text-risk-high",
    bg: "bg-risk-high/20",
    ring: "ring-risk-high/50",
    dot: "bg-risk-high",
    chip: "bg-risk-high/20 text-risk-high border-risk-high/50 font-bold",
  },
  elevated: {
    label: "Elevated",
    token: "var(--risk-elevated)",
    text: "text-risk-elevated",
    bg: "bg-risk-elevated/12",
    ring: "ring-risk-elevated/30",
    dot: "bg-risk-elevated",
    chip: "bg-risk-elevated/12 text-risk-elevated border-risk-elevated/25",
  },
  moderate: {
    label: "Moderate",
    token: "var(--risk-moderate)",
    text: "text-risk-moderate",
    bg: "bg-risk-moderate/12",
    ring: "ring-risk-moderate/30",
    dot: "bg-risk-moderate",
    chip: "bg-risk-moderate/15 text-risk-moderate border-risk-moderate/25",
  },
  low: {
    label: "Low Risk",
    token: "var(--risk-low)",
    text: "text-risk-low",
    bg: "bg-risk-low/12",
    ring: "ring-risk-low/30",
    dot: "bg-risk-low",
    chip: "bg-risk-low/12 text-risk-low border-risk-low/25",
  },
};

export function tierFromScore(score: number): RiskTier {
  // Hardcoded business-rule tiers (score is 0-100):
  //   0–30 %  → Low
  //   30–65 % → Moderate  (needs review)
  //   65–80 % → High
  //   80–100% → Critical
  if (score >= 80) return "critical";
  if (score >= 65) return "high";
  if (score >= 30) return "moderate";
  return "low";
}

export function tierColorVar(tier: RiskTier): string {
  const config = riskConfig[tier];
  if (!config) {
    console.warn(`[tierColorVar] Unrecognized risk tier: "${tier}"`);
    return "var(--muted-foreground)"; // safe fallback
  }
  return config.token;
}

export const statusConfig: Record<
  string,
  { label: string; chip: string; dot: string }
> = {
  submitted: { label: "Submitted", chip: "bg-muted text-muted-foreground border-border", dot: "bg-muted-foreground" },
  under_review: { label: "Under Review", chip: "bg-chart-4/12 text-chart-4 border-chart-4/25", dot: "bg-chart-4" },
  investigating: { label: "Investigating", chip: "bg-risk-elevated/12 text-risk-elevated border-risk-elevated/25", dot: "bg-risk-elevated" },
  flagged: { label: "Flagged", chip: "bg-risk-high/12 text-risk-high border-risk-high/25", dot: "bg-risk-high" },
  pending_documents: { label: "Pending Docs", chip: "bg-risk-moderate/15 text-risk-moderate border-risk-moderate/25", dot: "bg-risk-moderate" },
  investigated: { label: "Reviewed", chip: "bg-[#8b5cf6]/15 text-[#8b5cf6] border-[#8b5cf6]/25", dot: "bg-[#8b5cf6]" },
  approved: { label: "Approved", chip: "bg-risk-low/12 text-risk-low border-risk-low/25", dot: "bg-risk-low" },
  rejected: { label: "Rejected", chip: "bg-muted text-muted-foreground border-border", dot: "bg-muted-foreground" },
};

export const statusLabel = (s: string) => statusConfig[s]?.label ?? s;
