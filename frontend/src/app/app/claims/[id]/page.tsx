"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useAppData } from "@/lib/hooks/use-app-data";
import { inr, fmtDate, fmtDateTime, hoursBetween, relativeTime } from "@/lib/format";
import { statusLabel } from "@/lib/risk";
import { ScanModal } from "@/components/ui/scan-modal";
import { RiskBadge, StatusBadge, EmptyState, GlassPanel, PageHeader, PageTransition } from "@/components/ui/claimguard";
import { AnimatedNumber, FadeIn } from "@/components/ui/motion";
import { RiskGauge } from "@/components/ui/risk-gauge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft, FileText, Bot, Brain, Car, User, ShieldCheck,
  Clock, MapPin, AlertTriangle, CheckCircle2, Sparkles, RefreshCw,
  ChevronDown, ChevronUp, Flame, FileWarning, ShieldAlert, Info, TrendingUp
} from "lucide-react";

function getRuleIcon(rule: string) {
  if (rule.includes("INVALID")) return <ShieldAlert className="h-4 w-4 text-red-500" />;
  if (rule.includes("FIR") || rule.includes("WITNESS")) return <FileWarning className="h-4 w-4 text-amber-500" />;
  if (rule.includes("AI")) return <Bot className="h-4 w-4 text-purple-500" />;
  if (rule.includes("DATA") || rule.includes("MISSING") || rule.includes("WRONG")) return <AlertTriangle className="h-4 w-4 text-orange-500" />;
  if (rule.includes("MEDICAL") || rule.includes("DOCUMENT")) return <FileText className="h-4 w-4 text-blue-500" />;
  return <Info className="h-4 w-4 text-gray-500" />;
}

export default function ClaimDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { claimById } = useAppData();
  const claim = claimById(id);
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [shapExpanded, setShapExpanded] = useState(true);

  if (!claim) {
    return (
      <PageTransition>
        <PageHeader title="Claim not found" />
        <EmptyState
          title="Claim not found"
          description={`No claim matches "${id}". It may not exist or sample data is off.`}
          action={
            <Button asChild variant="outline" size="sm">
              <Link href="/app/claims">Back to claims</Link>
            </Button>
          }
        />
      </PageTransition>
    );
  }

  const p = claim.prediction as any;
  const s = claim.shap;
  const a = claim.agent;
  const ruleFlags = (claim as any).ruleFlags || [];

  // Humanize SHAP labels (data hook already provides label/description)
  const humanizedShap = s?.map((sh: any) => ({
    ...sh,
    direction: sh.contribution > 0 ? "increased" : "decreased",
    severity: Math.abs(sh.contribution) > 0.5 ? "strongly" : Math.abs(sh.contribution) > 0.2 ? "moderately" : "slightly",
  })) || [];

  // Sort by absolute contribution
  const sortedShap = [...humanizedShap].sort((a: any, b: any) => Math.abs(b.contribution) - Math.abs(a.contribution));

  // Calculate rule-based probability boost
  const ruleBoost = ruleFlags.length > 0
    ? ruleFlags.reduce((sum: number, f: any) => sum + (f.score_added || 0), 0)
    : 0;

  return (
    <PageTransition>
      <ScanModal
        isOpen={isScanOpen}
        onClose={() => setIsScanOpen(false)}
        claimId={claim.id}
        onComplete={() => window.location.reload()}
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-medium">{claim.claimNumber}</h1>
            <StatusBadge status={claim.status} />
          </div>
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{claim.description}</p>
        </div>
        <Button asChild variant="ghost" size="sm" className="gap-1.5">
          <Link href="/app/claims"><ArrowLeft className="h-4 w-4" /> Back</Link>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        {/* Left: prediction summary + links */}
        <div className="space-y-5">
          {p ? (
            <GlassPanel className="flex flex-col items-center p-6">
              <RiskGauge value={p.fraudProbability} tier={p.riskTier} size="md" label="Fraud risk" sublabel={p.riskTier.charAt(0).toUpperCase() + p.riskTier.slice(1)} />
              <div className="mt-4 grid w-full grid-cols-2 gap-3 text-center">
                <div className="rounded-xl bg-muted p-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Confidence</p>
                  <p className="nums text-sm font-semibold">{p.confidence}%</p>
                </div>
                <div className="rounded-xl bg-muted p-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Model</p>
                  <p className="text-[10px] font-medium text-muted-foreground">{p.modelVersion}</p>
                </div>
              </div>
              <div className="mt-4 w-full space-y-1">
                <Button asChild variant="outline" size="sm" className="w-full gap-1.5 justify-start">
                  <Link href={`/app/analysis?claim=${claim.id}`}><Brain className="h-3.5 w-3.5" /> Full analysis</Link>
                </Button>
                {a && (
                  <Button asChild variant="outline" size="sm" className="w-full gap-1.5 justify-start">
                    <Link href={`/app/investigation?claim=${claim.id}`}><FileText className="h-3.5 w-3.5" /> Investigation report</Link>
                  </Button>
                )}
                <Button onClick={() => setIsScanOpen(true)} variant="outline" size="sm" className="w-full gap-1.5 justify-start text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                  <RefreshCw className="h-3.5 w-3.5" /> Rescan for fraud
                </Button>
              </div>
            </GlassPanel>
          ) : (
            <GlassPanel className="flex flex-col items-center p-6 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
                <Clock className="h-6 w-6" />
              </div>
              <p className="mt-3 text-sm font-medium">Awaiting analysis</p>
              <p className="mt-1 text-xs text-muted-foreground mb-5">This claim has not been processed by the ML model yet.</p>
              <Button onClick={() => setIsScanOpen(true)} className="w-full gap-2 bg-blue-600 hover:bg-blue-700 text-white border-0">
                <Sparkles className="w-4 h-4" />
                Run AI Scan
              </Button>
            </GlassPanel>
          )}

          {/* Customer quick-info */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              <User className="h-3.5 w-3.5" /> Customer
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span className="font-medium">{claim.customer.name}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Location</span><span>{claim.customer.city || "—"}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Contact</span><span>{claim.customer.email || "—"}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">History</span><span>{claim.customer.previousClaims || 0} prev claims</span></div>
            </div>
          </div>

          {/* Vehicle */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              <Car className="h-3.5 w-3.5" /> Vehicle
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Make</span><span className="font-medium">{claim.vehicle.make} {claim.vehicle.model}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Year / Type</span><span className="nums">{claim.vehicle.year} {claim.vehicle.type ? `(${claim.vehicle.type})` : ""}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Reg / Color</span><span>{claim.vehicle.registrationNumber} {claim.vehicle.color ? `(${claim.vehicle.color})` : ""}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Market Value</span><span className="nums">{claim.vehicle.marketValue ? inr(claim.vehicle.marketValue, { compact: true }) : "—"}</span></div>
            </div>
          </div>
        </div>

        {/* Right: details + SHAP + AI explanation + rule flags */}
        <div className="space-y-6">
          {/* Incident details */}
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="mb-4 text-sm font-semibold">Incident details</h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { icon: Clock, label: "Incident date", value: fmtDateTime(claim.incidentDate) },
                { icon: Clock, label: "Reported", value: fmtDateTime(claim.reportedDate) },
                { icon: AlertTriangle, label: "Reporting delay", value: `${Math.round(hoursBetween(claim.incidentDate, claim.reportedDate) / 24)} days` },
                { icon: MapPin, label: "Location", value: claim.incidentLocation },
                { icon: ShieldCheck, label: "Type", value: (claim.type || "").replace(/_/g, " ") },
                { icon: AlertTriangle, label: "Witnesses", value: `${claim.witnessCount || 0}` },
              ].map((r) => (
                <div key={r.label}>
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{r.label}</p>
                  <p className="mt-1 text-sm font-medium">{r.value}</p>
                </div>
              ))}
            </div>
            <Separator className="my-4" />
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Claim amount</p>
                <p className="mt-1 text-lg font-heading font-medium text-brand nums">{inr(claim.claimAmount)}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Approved amount</p>
                <p className="mt-1 text-lg font-heading font-medium nums">{claim.approvedAmount ? inr(claim.approvedAmount) : "—"}</p>
              </div>
            </div>
            <Separator className="my-4" />
            <div className="flex flex-wrap gap-3 text-xs">
              {[
                { label: "Police report", ok: claim.hasPoliceReport },
                { label: "Witnesses", ok: claim.hasWitnesses, extra: claim.witnessCount > 0 ? `(${claim.witnessCount})` : "" },
                { label: "Medical bills", ok: claim.hasMedicalBills },
                { label: "Repair bills", ok: claim.hasRepairBills },
              ].map((d) => (
                <span key={d.label} className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 ${d.ok ? "border-risk-low/25 bg-risk-low/10 text-risk-low" : "border-risk-high/25 bg-risk-high/10 text-risk-high"}`}>
                  {d.ok ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                  {d.label} {d.extra ?? ""}
                </span>
              ))}
              <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-0.5 text-muted-foreground">
                {claim.documentsCount} documents
              </span>
            </div>
          </div>

          {/* AI Explanation Panel */}
          {p?.explanation && (
            <div className="rounded-2xl border border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950/30 dark:to-indigo-950/30 dark:border-purple-800/30 p-6">
              <div className="mb-4 flex items-center gap-2">
                <Bot className="h-4 w-4 text-purple-600" />
                <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-200">AI Fraud Analysis</h3>
                <Badge variant="secondary" className="ml-auto text-[10px] bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
                  AI Generated
                </Badge>
              </div>
              <p className="text-sm text-purple-800 dark:text-purple-200 leading-relaxed">{p.explanation}</p>
            </div>
          )}

          {/* Rule Flags Panel */}
          {ruleFlags.length > 0 && (
            <div className="rounded-2xl border border-red-200 bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/30 dark:to-orange-950/30 dark:border-red-800/30 p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-red-500" />
                  <h3 className="text-sm font-semibold text-red-900 dark:text-red-200">Fraud Rule Flags</h3>
                  <Badge variant="secondary" className="text-[10px] bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300">
                    {ruleFlags.length} trigger{ruleFlags.length !== 1 ? "s" : ""}
                  </Badge>
                </div>
                <span className="text-xs text-red-600 dark:text-red-300 font-medium">
                  +{Math.round(ruleBoost * 100)}% total boost
                </span>
              </div>
              <div className="space-y-2.5">
                {ruleFlags.map((flag: any, i: number) => (
                  <FadeIn key={`${flag.rule}-${i}`} delay={i * 0.05}>
                    <div className="flex items-start gap-3 rounded-xl bg-white/60 dark:bg-white/5 p-3 border border-red-100/50 dark:border-red-800/20">
                      <div className="mt-0.5 shrink-0">{getRuleIcon(flag.rule)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{flag.label}</span>
                          <Badge variant="secondary" className="text-[9px] px-1.5 py-0 bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300">
                            +{Math.round(flag.score_added * 100)}%
                          </Badge>
                        </div>
                        <p className="mt-0.5 text-xs text-gray-600 dark:text-gray-400 leading-relaxed">{flag.reason}</p>
                      </div>
                    </div>
                  </FadeIn>
                ))}
              </div>
            </div>
          )}

          {/* SHAP breakdown — Humanized */}
          {sortedShap.length > 0 && (
            <div className="rounded-2xl border border-border bg-card p-6">
              <button
                onClick={() => setShapExpanded(!shapExpanded)}
                className="mb-4 flex w-full items-center gap-2 text-left"
              >
                <Brain className="h-4 w-4 text-brand" />
                <h3 className="text-sm font-semibold">What influenced this prediction?</h3>
                <Badge variant="secondary" className="ml-auto text-[10px]">{p?.modelVersion}</Badge>
                {shapExpanded ? <ChevronUp className="h-4 w-4 ml-1" /> : <ChevronDown className="h-4 w-4 ml-1" />}
              </button>
              {shapExpanded && (
                <div className="space-y-4">
                  <p className="text-xs text-muted-foreground mb-4 leading-relaxed">
                    Each factor below shows how it affected the fraud prediction.
                    <span className="text-risk-high"> Red factors increased</span> the risk,
                    <span className="text-risk-low"> green factors decreased</span> it.
                  </p>
                  {sortedShap.map((sh: any, i: number) => {
                    const increases = sh.contribution > 0;
                    return (
                      <FadeIn key={sh.feature} delay={i * 0.04}>
                        <div className="space-y-1.5">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <span className="text-xs font-medium text-foreground/90">{sh.label}</span>
                              {sh.description && (
                                <p className="text-[10px] text-muted-foreground/70 leading-snug mt-0.5">{sh.description}</p>
                              )}
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="text-muted-foreground text-[10px]">
                                {sh.severity} {sh.direction} risk
                              </span>
                              <span className={`nums font-semibold text-xs ${increases ? "text-risk-high" : "text-risk-low"}`}>
                                {increases ? "↑" : "↓"} {Math.abs(sh.contribution).toFixed(2)}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                              <div
                                className={`h-full rounded-full transition-all ${increases ? "bg-risk-high" : "bg-risk-low"}`}
                                style={{ width: `${Math.min(Math.abs(sh.contribution) / 2.0 * 100, 100)}%` }}
                              />
                            </div>
                            <span className="text-[9px] text-muted-foreground/60 shrink-0 w-24 text-right">
                              {increases ? "Raises" : "Lowers"} fraud risk
                            </span>
                          </div>
                        </div>
                      </FadeIn>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Agent summary */}
          {a && (
            <div className="rounded-2xl border border-brand/20 bg-brand/5 p-6">
              <div className="mb-4 flex items-center gap-2">
                <Bot className="h-4 w-4 text-brand" />
                <h3 className="text-sm font-semibold">AI Agent investigation</h3>
                <Badge variant="secondary" className="ml-auto text-[10px]">Confidence {a.confidenceLevel}%</Badge>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{a.orchestratorSummary}</p>
              <Separator className="my-4" />
              <div className="mb-3 text-xs font-medium">Recommended actions</div>
              <ul className="space-y-2">
                {a.recommendedActions.map((act: string) => (
                  <li key={act} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" /> {act}
                  </li>
                ))}
              </ul>
              {a.missingDocuments.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <div className="mb-3 text-xs font-medium">Missing documents</div>
                  <ul className="space-y-1.5">
                    {a.missingDocuments.map((d: string) => (
                      <li key={d} className="flex items-center gap-2 text-sm text-risk-elevated">
                        <AlertTriangle className="h-3.5 w-3.5" /> {d}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              {a.ruleViolations.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <div className="mb-3 text-xs font-medium">Rule violations</div>
                  <ul className="space-y-1.5">
                    {a.ruleViolations.map((rv: any) => (
                      <li key={rv.rule} className="flex items-start gap-2 text-sm">
                        <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${rv.severity === "critical" ? "bg-risk-high" : rv.severity === "warning" ? "bg-risk-moderate" : "bg-chart-4"}`} />
                        <div>
                          <span className="font-medium">{rv.rule}</span>
                          <span className="text-muted-foreground"> — {rv.detail}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {/* Investigator Feedback */}
          {p && claim.feedback && claim.feedback.length > 0 ? (
            <div className="rounded-2xl border border-[#8b5cf6]/30 bg-[#8b5cf6]/5 p-6">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="h-5 w-5 text-[#8b5cf6]" />
                <h3 className="text-sm font-semibold text-[#8b5cf6]">Investigation Complete</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Final Decision</div>
                  <div className="font-medium">{claim.feedback[0].final_decision}</div>
                </div>
                {claim.feedback[0].investigation_notes && (
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Investigation Notes</div>
                    <div className="text-sm">{claim.feedback[0].investigation_notes}</div>
                  </div>
                )}
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Reviewed At</div>
                  <div className="text-sm">{new Date(claim.feedback[0].timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })}</div>
                </div>
              </div>
            </div>
          ) : p ? (
            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="mb-4 text-sm font-semibold">Investigator Decision</h3>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.target as HTMLFormElement;
                  const data = new FormData(form);
                  const decision = data.get('decision') as string;
                  const isFraud = decision === 'Fraud Confirmed';

                  try {
                    const { intelligenceApi } = await import('@/lib/intelligenceClient');
                    await intelligenceApi.submitFeedback({
                      claim_id: claim.id,
                      prediction_id: (p as any).id || claim.id,
                      final_decision: decision,
                      investigation_notes: data.get('notes') as string,
                      fraud_confirmed: isFraud,
                      claim_approved: !isFraud,
                    });
                    alert('Feedback submitted successfully!');
                    window.location.reload();
                  } catch (err: any) {
                    const msg = err.response?.data?.detail || err.message || "Unknown error";
                    alert(`Failed to submit feedback: ${msg}`);
                  }
                }}
                className="space-y-4 text-sm"
              >
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Final Decision</label>
                  <select name="decision" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" required>
                    <option value="">Select decision...</option>
                    <option value="Fraud Confirmed">Fraud Confirmed</option>
                    <option value="Genuine Claim">Genuine Claim</option>
                    <option value="Inconclusive">Inconclusive (Needs further review)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Investigation Notes</label>
                  <textarea name="notes" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" rows={3} placeholder="Enter your rationale for this decision..." required></textarea>
                </div>
                <Button type="submit" className="w-full">Submit Feedback</Button>
              </form>
            </div>
          ) : null}
        </div>
      </div>
    </PageTransition>
  );
}
