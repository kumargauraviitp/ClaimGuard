"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppData } from "@/lib/hooks/use-app-data";
import { Suspense } from "react";
import { RiskGauge } from "@/components/ui/risk-gauge";
import { FadeIn, MotionStagger, MotionItem } from "@/components/ui/motion";
import { EmptyState, GlassPanel, PageHeader, PageTransition, GradientBorderPanel } from "@/components/ui/claimguard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Brain, GitBranch, AlertTriangle, Bot, ShieldAlert } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function FraudAnalysisContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const data = useAppData();

  const analyzedClaims = data.claims.filter(c => c.prediction && c.shap && c.shap.length > 0);
  const defaultClaimId = analyzedClaims.length > 0 ? analyzedClaims[0].id : null;
  const claimId = searchParams.get("claim") || defaultClaimId;
  const claim = claimId ? data.claimById(claimId) : null;

  if (!claim?.prediction || !claim.shap) {
    return (
      <PageTransition>
        <PageHeader title="Fraud Analysis" description="ML + SHAP breakdown" />
        <EmptyState
          icon={<Brain className="h-6 w-6" />}
          title="No analysis available"
          description="We couldn't find any scored claims in the system yet."
          action={<Button asChild size="sm"><Link href="/app/claims">Browse claims</Link></Button>}
        />
      </PageTransition>
    );
  }

  const { prediction: p, shap: s } = claim;
  const positive = s.filter((f) => f.contribution > 0).sort((a, b) => b.contribution - a.contribution);
  const negative = s.filter((f) => f.contribution < 0).sort((a, b) => a.contribution - b.contribution);
  const maxAbs = Math.max(...s.map((f) => Math.abs(f.contribution)));

  const isHighRisk = p.riskTier === "high" || p.riskTier === "critical";
  const glowColor = isHighRisk ? "var(--risk-high)" : p.riskTier === "moderate" || p.riskTier === "elevated" ? "var(--risk-elevated)" : "var(--risk-low)";

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Intelligence"
        title="Fraud Analysis"
        description="Deep dive into the ML decision engine"
        action={
          <div className="flex items-center gap-4">
            {analyzedClaims.length > 0 && (
              <Select value={claim.id} onValueChange={(val) => router.push(`?claim=${val}`)}>
                <SelectTrigger className="w-[300px] h-9">
                  <SelectValue placeholder="Select a claim to analyze" />
                </SelectTrigger>
                <SelectContent>
                  {analyzedClaims.map(c => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.claimNumber} — {c.customer.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Button asChild variant="outline" size="sm" className="gap-1.5 h-9">
              <Link href={`/app/claims/${claim.id}`}><ArrowLeft className="h-4 w-4" /> View full claim</Link>
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        {/* Left: gauge + summary */}
        <div className="space-y-6">
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-8 shadow-2xl">
            {/* Ambient Background Glow */}
            <div
              className="absolute -top-40 -right-40 h-80 w-80 rounded-full opacity-20 blur-[100px] pointer-events-none transition-colors duration-1000"
              style={{ backgroundColor: glowColor }}
            />
            <div
              className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full opacity-10 blur-[100px] pointer-events-none transition-colors duration-1000"
              style={{ backgroundColor: glowColor }}
            />

            <div className="relative z-10 flex flex-col items-center">
              <RiskGauge value={p.fraudProbability} tier={p.riskTier || 'moderate'} size="lg" label="Fraud probability" sublabel={(p.riskTier || 'moderate').charAt(0).toUpperCase() + (p.riskTier || 'moderate').slice(1)} />

              <div className="mt-8 w-full grid grid-cols-3 gap-3">
                <div className="flex flex-col items-center justify-center rounded-xl bg-white/5 border border-white/5 p-4 backdrop-blur-md">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground/80 font-semibold mb-1">Confidence</p>
                  <p className="nums text-xl font-bold text-foreground drop-shadow-md">{p.confidence}%</p>
                </div>
                <div className="flex flex-col items-center justify-center rounded-xl bg-white/5 border border-white/5 p-4 backdrop-blur-md">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground/80 font-semibold mb-1">Signals</p>
                  <p className="nums text-xl font-bold text-foreground drop-shadow-md">{s.length}</p>
                </div>
                <div className="flex flex-col items-center justify-center rounded-xl bg-white/5 border border-white/5 p-4 backdrop-blur-md">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground/80 font-semibold mb-1">Model</p>
                  <p className="text-xs font-medium text-foreground drop-shadow-md">{p.modelVersion.split(" ")[0]}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Assessment Summary */}
          <GlassPanel className="p-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full" style={{ backgroundColor: glowColor }} />
            <div className="flex items-center gap-2 mb-3">
              <GitBranch className="h-4 w-4 text-brand" />
              <h3 className="text-sm font-semibold">Executive summary</h3>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {p.riskTier === "high" || p.riskTier === "critical" ? `This claim exhibits a very high probability of fraud (${p.fraudProbability}%). Multiple independent risk signals have converged — the ML model and SHAP analysis both indicate this requires immediate investigation.` : ""}
              {p.riskTier === "elevated" && `This claim presents elevated risk (${p.fraudProbability}%). While not definitively fraudulent, several factors warrant further review by an investigator.`}
              {p.riskTier === "moderate" && `This claim has a moderate fraud probability (${p.fraudProbability}%). Some indicators are flagged but the overall risk profile is within acceptable parameters.`}
              {p.riskTier === "low" && `This claim shows a low fraud probability (${p.fraudProbability}%). The features driving this prediction are consistent with a genuine claim.`}
            </p>
          </GlassPanel>

          {/* AI Fraud Analysis */}
          {claim.agent?.orchestratorSummary && (
            <GlassPanel className="p-6">
              <div className="flex items-center gap-2 mb-3">
                <Bot className="h-4 w-4 text-brand" />
                <h3 className="text-sm font-semibold">AI Fraud Analysis</h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {claim.agent.orchestratorSummary}
              </p>
            </GlassPanel>
          )}

          {/* Fraud Rule Flags */}
          {claim.agent?.ruleViolations && claim.agent.ruleViolations.length > 0 && (
            <GlassPanel className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <ShieldAlert className="h-4 w-4 text-risk-high" />
                <h3 className="text-sm font-semibold">Fraud Rule Flags</h3>
              </div>
              <div className="space-y-3">
                {claim.agent.ruleViolations.map((v: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-3 rounded-xl bg-white/5 border border-white/5 p-3">
                    <div className={`mt-0.5 rounded-full p-1.5 ${v.severity === "critical" ? "bg-risk-high/20 text-risk-high" : "bg-risk-elevated/20 text-risk-elevated"}`}>
                      <AlertTriangle className="h-3 w-3" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-foreground/90">{v.rule}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{v.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </GlassPanel>
          )}
        </div>

        {/* Right: SHAP waterfall */}
        <div className="space-y-6">
          <GlassPanel className="p-6">
            <div className="flex flex-col mb-8">
              <div className="flex items-center gap-2 mb-1">
                <Brain className="h-4 w-4 text-brand" />
                <h3 className="text-sm font-semibold">SHAP contribution drivers</h3>
              </div>
              <p className="text-xs text-muted-foreground">How each specific attribute pushed the final fraud probability up (red) or down (green).</p>
            </div>

            <MotionStagger className="space-y-3" stagger={0.06}>
              {[...positive, ...negative].map((f) => {
                const pct = Math.abs(f.contribution) / maxAbs;
                const isPos = f.contribution > 0;

                return (
                  <MotionItem key={f.feature}>
                    <div className="group relative flex items-center gap-4 rounded-xl border border-white/[0.03] bg-white/[0.02] p-3 transition-colors hover:bg-white/[0.04]">
                      <div className="w-[180px] shrink-0">
                        <p className="text-sm font-medium text-foreground/90 truncate" title={f.label}>{f.label}</p>
                        {(f as any).description && <p className="text-[10px] text-muted-foreground/70 leading-snug mt-0.5 truncate" title={(f as any).description}>{(f as any).description}</p>}
                        <p className="text-[10px] text-muted-foreground nums uppercase tracking-wider mt-0.5">{f.value}</p>
                      </div>

                      <div className="flex-1 flex items-center">
                        {isPos ? (
                          <div className="flex-1 flex justify-end relative">
                            <div className="absolute inset-y-0 right-0 border-r border-risk-high/30 h-full -mr-1" />
                            <div
                              className={`h-8 rounded-l-md bg-gradient-to-l flex items-center justify-end px-3 shadow-lg ${f.category === 'amount' ? 'from-rose-500 to-rose-500/10 shadow-rose-500/20' :
                                  f.category === 'policy' ? 'from-orange-500 to-orange-500/10 shadow-orange-500/20' :
                                    f.category === 'behavior' ? 'from-purple-500 to-purple-500/10 shadow-purple-500/20' :
                                      f.category === 'vehicle' ? 'from-pink-500 to-pink-500/10 shadow-pink-500/20' :
                                        f.category === 'history' ? 'from-red-500 to-red-500/10 shadow-red-500/20' :
                                          'from-risk-high to-risk-high/10 shadow-[var(--risk-high)]/20'
                                }`}
                              style={{ width: `${pct * 100}%`, minWidth: "60px" }}
                            >
                              <span className="nums text-xs font-bold text-white drop-shadow-md">+{f.contribution.toFixed(1)}%</span>
                            </div>
                          </div>
                        ) : (
                          <div className="flex-1 flex relative">
                            <div className="absolute inset-y-0 left-0 border-l border-risk-low/30 h-full -ml-1" />
                            <div
                              className={`h-8 rounded-r-md bg-gradient-to-r flex items-center px-3 shadow-lg ${f.category === 'amount' ? 'from-emerald-500 to-emerald-500/10 shadow-emerald-500/20' :
                                  f.category === 'policy' ? 'from-teal-500 to-teal-500/10 shadow-teal-500/20' :
                                    f.category === 'behavior' ? 'from-cyan-500 to-cyan-500/10 shadow-cyan-500/20' :
                                      f.category === 'vehicle' ? 'from-lime-500 to-lime-500/10 shadow-lime-500/20' :
                                        f.category === 'history' ? 'from-green-500 to-green-500/10 shadow-green-500/20' :
                                          'from-risk-low to-risk-low/10 shadow-[var(--risk-low)]/20'
                                }`}
                              style={{ width: `${pct * 100}%`, minWidth: "60px" }}
                            >
                              <span className="nums text-xs font-bold text-white drop-shadow-md">{f.contribution.toFixed(1)}%</span>
                            </div>
                          </div>
                        )}
                      </div>

                      <Badge variant="outline" className="w-20 justify-center text-[10px] capitalize shrink-0 bg-black/40 backdrop-blur-sm border-white/10">
                        {f.category === "behavior" ? "behave" : (f.category ? f.category.slice(0, 5) : "other")}
                      </Badge>
                    </div>
                  </MotionItem>
                );
              })}
            </MotionStagger>

            <Separator className="my-6 bg-white/10" />

            <div className="flex items-center justify-between rounded-xl bg-white/5 border border-white/5 p-4">
              <span className="text-sm text-muted-foreground font-medium">Final ML Prediction</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground">Base + Drivers =</span>
                <span className="nums text-xl font-bold drop-shadow-sm" style={{ color: glowColor }}>{p.fraudProbability}%</span>
              </div>
            </div>
          </GlassPanel>
        </div>
      </div>
    </PageTransition>
  );
}

export default function FraudAnalysisPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-muted-foreground">Loading analysis…</div>}>
      <FraudAnalysisContent />
    </Suspense>
  );
}
