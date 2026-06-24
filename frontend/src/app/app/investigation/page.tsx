"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from "react";
import { useAppData } from "@/lib/hooks/use-app-data";
import { RiskGauge } from "@/components/ui/risk-gauge";
import { FadeIn } from "@/components/ui/motion";
import { EmptyState, GradientBorderPanel, PageHeader, PageTransition, StatusBadge } from "@/components/ui/claimguard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { FileText, ArrowLeft, Download, Printer, AlertTriangle, CheckCircle2, Bot, Clock } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function InvestigationReportContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const data = useAppData();

  const investigatedClaims = data.claims.filter(c => c.prediction && c.agent);
  const defaultClaimId = investigatedClaims.length > 0 ? investigatedClaims[0].id : null;
  const claimId = searchParams.get("claim") || defaultClaimId;
  const claim = claimId ? data.claimById(claimId) : null;
  const agent = claim?.agent;

  if (!agent || !claim?.prediction) {
    return (
      <PageTransition>
        <PageHeader title="Investigation Report" description="AI-generated investigation report" />
        <EmptyState
          icon={<FileText className="h-6 w-6" />}
          title="No report available"
          description="We couldn't find any investigated claims in the system yet."
          action={<Button asChild size="sm"><Link href="/app/claims">Browse claims</Link></Button>}
        />
      </PageTransition>
    );
  }

  const recColor = agent.finalRecommendation === "approve" ? "text-risk-low" : agent.finalRecommendation === "reject" ? "text-risk-high" : "text-risk-elevated";

  return (
    <PageTransition>
      <div className="print:bg-white print:text-black">
      <PageHeader
        eyebrow="Intelligence"
        title="Investigation Report"
        description={`${claim.claimNumber} — Generated ${agent.generatedAt ? new Date(agent.generatedAt).toLocaleString("en-IN") : ""}`}
        action={
          <div className="flex gap-2 print:hidden">
            {investigatedClaims.length > 0 && (
              <Select value={claim.id} onValueChange={(val) => router.push(`?claim=${val}`)}>
                <SelectTrigger className="w-[260px] h-9">
                  <SelectValue placeholder="Select claim" />
                </SelectTrigger>
                <SelectContent>
                  {investigatedClaims.map(c => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.claimNumber} — {c.customer.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Button variant="outline" size="sm" className="gap-1.5 h-9" onClick={() => window.print()}>
              <Printer className="h-3.5 w-3.5" /> Print
            </Button>
            <Button size="sm" className="gap-1.5 bg-brand text-primary-foreground hover:bg-brand/90 h-9" onClick={() => window.print()}>
              <Download className="h-3.5 w-3.5" /> Export PDF
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="space-y-6">
          {/* Header card */}
          <GradientBorderPanel className="bg-card print:border-gray-200">
            <div className="p-6">
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="font-heading text-xl font-medium">{claim.claimNumber}</span>
                <StatusBadge status={claim.status} />
                <Badge variant="secondary" className="text-[10px] print:border-gray-300">v4.2</Badge>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="text-center">
                  <RiskGauge value={claim.prediction!.fraudProbability} tier={claim.prediction!.riskTier} size="sm" showHalo={false} />
                </div>
                <div className="text-center">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">Confidence</p>
                  <p className="font-heading text-3xl font-medium nums">{agent.confidenceLevel}%</p>
                </div>
                <div className="text-center">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">Recommendation</p>
                  <p className={`font-heading text-lg font-medium capitalize ${recColor} print:font-bold`}>{agent.finalRecommendation.replace(/_/g, " ")}</p>
                </div>
              </div>
            </div>
          </GradientBorderPanel>

          {/* Customer Details */}
          <div className="rounded-2xl border border-border bg-card p-6 print:border-gray-200 hidden print:block mb-6">
            <h3 className="text-sm font-semibold mb-4">Customer Details</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground mb-1">Name</p>
                <p className="font-medium">{claim.customer.name}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-1">Phone Number</p>
                <p className="font-medium">{claim.customer.phone || "Not provided"}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-1">Email ID</p>
                <p className="font-medium">{claim.customer.email || "Not provided"}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-1">Location</p>
                <p className="font-medium">{claim.customer.city}{claim.customer.state !== "—" ? `, ${claim.customer.state}` : ""}</p>
              </div>
            </div>
          </div>

          {/* Orchestrator summary */}
          <div className="rounded-2xl border border-border bg-card p-6 print:border-gray-200">
            <h3 className="text-sm font-semibold mb-3">Orchestrator summary</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{agent.orchestratorSummary}</p>
          </div>

          {/* Risk analysis */}
          <div className="rounded-2xl border border-border bg-card p-6 print:border-gray-200">
            <h3 className="text-sm font-semibold mb-3">Risk analysis</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{agent.riskAnalysis}</p>
          </div>

          {/* Recommended actions */}
          <div className="rounded-2xl border border-border bg-card p-6 print:border-gray-200">
            <h3 className="text-sm font-semibold mb-4">Recommended investigation actions</h3>
            <ul className="space-y-3">
              {agent.recommendedActions.map((a, i) => (
                <FadeIn key={i} delay={i * 0.05} className="print:opacity-100 print:transform-none">
                  <li className="flex items-start gap-3 text-sm">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand text-xs font-bold nums print:bg-gray-100 print:text-black print:border print:border-gray-300">{i + 1}</span>
                    <span className="text-muted-foreground">{a}</span>
                  </li>
                </FadeIn>
              ))}
            </ul>
          </div>

          {/* Missing documents */}
          {agent.missingDocuments.length > 0 && (
            <div className="rounded-2xl border border-risk-elevated/20 bg-risk-elevated/5 p-6 print:border-gray-200 print:bg-white">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-risk-elevated" /> Missing documents</h3>
              <ul className="space-y-2">
                {agent.missingDocuments.map((d) => (
                  <li key={d} className="flex items-center gap-2 text-sm text-risk-elevated print:text-gray-800"><AlertTriangle className="h-3.5 w-3.5 shrink-0" />{d}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggested verification steps */}
          <div className="rounded-2xl border border-border bg-card p-6 print:border-gray-200">
            <h3 className="text-sm font-semibold mb-3">Suggested verification steps</h3>
            <ul className="space-y-2">
              {agent.suggestedVerificationSteps.map((s) => (
                <li key={s} className="flex items-start gap-2 text-sm text-muted-foreground"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-chart-4 print:text-gray-600" />{s}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Sidebar: rule violations + agent trace */}
        <div className="space-y-6">
          {/* Rule violations */}
          {agent.ruleViolations.length > 0 && (
            <div className="rounded-2xl border border-border bg-card p-5 print:border-gray-200">
              <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider text-muted-foreground">Rule violations</h4>
              <div className="space-y-3">
                {agent.ruleViolations.map((rv) => (
                  <div key={rv.rule} className={`rounded-xl border p-3 ${rv.severity === "critical" ? "border-risk-high/30 bg-risk-high/5" : rv.severity === "warning" ? "border-risk-moderate/30 bg-risk-moderate/5" : "border-chart-4/30 bg-chart-4/5"} print:bg-white print:border-gray-200`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`h-2 w-2 rounded-full ${rv.severity === "critical" ? "bg-risk-high" : rv.severity === "warning" ? "bg-risk-moderate" : "bg-chart-4"}`} />
                      <span className="text-xs font-semibold">{rv.rule}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{rv.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agent trace */}
          <div className="rounded-2xl border border-border bg-card p-5 print:border-gray-200 print:break-inside-avoid">
            <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider text-muted-foreground">Agent execution trace</h4>
            <div className="space-y-3">
              {agent.agentTrace.map((at) => (
                <div key={at.agent} className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted print:bg-gray-100 print:border print:border-gray-300">
                    <Bot className="h-3.5 w-3.5 text-brand print:text-black" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{at.agent}</span>
                      <span className="nums text-[10px] text-muted-foreground">{at.durationMs}ms</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground">{at.role}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{at.finding}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick info */}
          <div className="rounded-2xl border border-border bg-card p-5 print:border-gray-200 print:break-inside-avoid">
            <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider text-muted-foreground">Claim info</h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-muted-foreground">Customer</span><span>{claim.customer.name}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Amount</span><span className="nums">₹{(claim.claimAmount / 100000).toFixed(1)}L</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Region</span><span>{claim.region}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Assigned</span><span>{claim.assignedTo ?? "—"}</span></div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </PageTransition>
  );
}

export default function InvestigationReportPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-muted-foreground">Loading report…</div>}>
      <InvestigationReportContent />
    </Suspense>
  );
}
