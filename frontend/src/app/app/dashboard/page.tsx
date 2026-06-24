"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { useAppData } from "@/lib/hooks/use-app-data";
import { useAuthStore } from "@/lib/authStore";
import { inr, pctRaw, pct, compactNum, relativeTime, fmtDate } from "@/lib/format";
import { AnimatedNumber, FadeIn, MotionStagger, MotionItem } from "@/components/ui/motion";
import { RiskBadge, StatusBadge, EmptyState, GlassPanel, Sparkline } from "@/components/ui/claimguard";
import { PageHeader, PageTransition } from "@/components/layout/page";
import { Button } from "@/components/ui/button";
import { ChartContainer } from "@/components/ui/chart-container";
import {
  Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import {
  TrendingUp, ShieldCheck, AlertTriangle, Clock, ArrowUpRight,
  Brain, FileText, Activity, Bot, FilePlus2
} from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { humanizeFeature } from "@/lib/shap-labels";

export default function DashboardPage() {
  const [trendInterval, setTrendInterval] = useState("monthly");
  const data = useAppData(trendInterval);
  const { user } = useAuthStore();
  const isCustomer = user?.roles?.some(r => r.toLowerCase() === "customer");

  if (data.disconnected) {
    return (
      <PageTransition>
        <PageHeader title="Dashboard" description="Operations overview" />
        <EmptyState
          icon={<Activity className="h-6 w-6" />}
          title="No data connected"
          description="Enable sample data in Admin → System, or connect your backend."
          action={
            <Button asChild size="sm">
              <Link href="/app/admin">Open admin panel</Link>
            </Button>
          }
        />
      </PageTransition>
    );
  }

  const { kpis, claims, fraudTrend, fraudDistribution } = data;

  const highRiskClaims = claims
    .filter((c) => c.prediction && c.prediction.fraudProbability >= 45)
    .sort((a, b) => (b.prediction?.fraudProbability ?? 0) - (a.prediction?.fraudProbability ?? 0))
    .slice(0, 5);

  const recentClaims = [...claims].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );

  // We now rely on the backend kpis.fraudDetected directly.

  if (isCustomer) {
    return (
      <PageTransition>
        <PageHeader
          eyebrow="Workspace"
          title={`Welcome, ${user?.full_name?.split(' ')[0] || 'Customer'}!`}
          description="Manage your claims and view their statuses."
        />

        {/* KPI bento for Customer */}
        <MotionStagger className="mb-8 grid gap-4 sm:grid-cols-3 lg:grid-cols-3" stagger={0.04}>
          <MotionItem>
            <KpiCard
              label="Total Claims"
              value={<AnimatedNumber value={kpis.totalClaims || 0} format={(n) => num(Math.round(n))} />}
              icon={<ShieldCheck className="h-4 w-4" />}
              iconColor="text-brand"
            />
          </MotionItem>
          <MotionItem>
            <KpiCard
              label="Pending Processing"
              value={<AnimatedNumber value={kpis.openInvestigations || 0} format={(n) => num(Math.round(n))} />}
              icon={<Clock className="h-4 w-4" />}
              iconColor="text-yellow-500"
            />
          </MotionItem>
          <MotionItem>
            <KpiCard
              label="Completed"
              value={<AnimatedNumber value={(kpis.totalClaims - kpis.openInvestigations) || 0} format={(n) => num(Math.round(n))} />}
              icon={<Activity className="h-4 w-4" />}
              iconColor="text-green-500"
            />
          </MotionItem>
        </MotionStagger>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Recent Claims */}
          <GlassPanel className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold">Your Recent Claims</h3>
                <p className="text-xs text-muted-foreground">Status of your latest claims</p>
              </div>
              <Button asChild variant="ghost" size="sm" className="gap-1 text-xs">
                <Link href="/app/claims">
                  View all <ArrowUpRight className="h-3 w-3" />
                </Link>
              </Button>
            </div>
            <div className="space-y-3">
              {recentClaims.slice(0, 5).map((c) => (
                <Link
                  key={c.id}
                  href={`/app/claims/${c.id}`}
                  className="flex items-center justify-between rounded-xl border border-border p-3 transition-colors hover:border-brand/30 hover:bg-accent/40"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm nums">{c.claimNumber}</span>
                      <StatusBadge status={c.status} />
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{inr(c.claimAmount, { compact: true })}</span>
                      <span className="text-border">·</span>
                      <span>{fmtDate(c.incidentDate)}</span>
                    </div>
                  </div>
                </Link>
              ))}
              {recentClaims.length === 0 && (
                <div className="text-center text-sm text-muted-foreground py-4">
                  No claims filed yet.
                </div>
              )}
            </div>
          </GlassPanel>

          {/* Quick Actions */}
          <GlassPanel className="p-6 flex flex-col justify-center items-center text-center">
            <div className="mb-6 flex items-center gap-2 text-brand">
              <FilePlus2 className="h-10 w-10" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Need to file a new claim?</h3>
            <p className="text-sm text-muted-foreground mb-6">Provide the incident details and necessary documents to start the claims process.</p>
            <Button asChild size="lg" className="w-full max-w-[200px] rounded-full">
              <Link href="/app/claims/new">File a Claim</Link>
            </Button>
          </GlassPanel>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Workspace"
        title="Dashboard"
        description="Investigation operations overview"
      />

      {/* KPI bento */}
      <MotionStagger className="mb-8 grid gap-4 sm:grid-cols-3 lg:grid-cols-3" stagger={0.04}>
        <MotionItem>
          <KpiCard
            label="Total claims"
            value={<AnimatedNumber value={kpis.totalClaims} format={(n) => compactNum(Math.round(n))} />}
            change={`+${pct(Math.min(1, kpis.fraudRate))} fraud`}
            icon={<ShieldCheck className="h-4 w-4" />}
            iconColor="text-brand"
          />
        </MotionItem>
        <MotionItem>
          <KpiCard
            label="Fraud detected"
            value={<AnimatedNumber value={kpis.fraudDetected} format={(n) => num(Math.round(n))} />}
            change={`${(kpis.falsePositiveRate * 100).toFixed(1)}% FPR`}
            icon={<AlertTriangle className="h-4 w-4" />}
            iconColor="text-risk-high"
          />
        </MotionItem>
        <MotionItem>
          <KpiCard
            label="Open investigations"
            value={<AnimatedNumber value={kpis.openInvestigations} format={(n) => num(Math.round(n))} />}
            change={`${kpis.fraudDetected} flagged`}
            icon={<Clock className="h-4 w-4" />}
            iconColor="text-risk-elevated"
          />
        </MotionItem>
      </MotionStagger>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* Fraud trend chart */}
        <GlassPanel className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold">Fraud probability trend</h3>
              <p className="text-xs text-muted-foreground">{trendInterval.charAt(0).toUpperCase() + trendInterval.slice(1)} fraud rate & claim volume</p>
            </div>
            <Select value={trendInterval} onValueChange={setTrendInterval}>
              <SelectTrigger className="h-8 w-[120px] text-xs">
                <SelectValue placeholder="Select interval" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="yearly">Yearly</SelectItem>
                <SelectItem value="custom">Custom Date</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <ChartContainer height={240}>
            <AreaChart data={fraudTrend} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
              <defs>
                <linearGradient id="fraudFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                domain={[0, "auto"]}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "12px",
                  fontSize: 12,
                  color: "var(--foreground)",
                }}
                formatter={(value: any, name: any) => [
                  name === "fraudRate" ? `${(Number(value) * 100).toFixed(1)}%` : value,
                  name === "fraudRate" ? "Fraud rate" : "Volume",
                ]}
              />
              <Area type="monotone" dataKey="claimVolume" stroke="var(--chart-4)" fill="none" strokeWidth={1.5} strokeDasharray="4 3" />
              <Area type="monotone" dataKey="fraudRate" stroke="var(--chart-1)" fill="url(#fraudFill)" strokeWidth={2} />
            </AreaChart>
          </ChartContainer>
        </GlassPanel>

        {/* Claim type distribution */}
        <GlassPanel className="p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold">Fraud by claim type</h3>
              <p className="text-xs text-muted-foreground">Distribution of detected fraud cases</p>
            </div>
          </div>
          <div className="space-y-5">
            {(() => {
              const total = fraudDistribution.reduce((sum, item) => sum + item.value, 0) || 1;
              const max = Math.max(...fraudDistribution.map(d => d.value)) || 1;

              return fraudDistribution.map((item, idx) => {
                const percentOfMax = (item.value / max) * 100;
                const percentOfTotal = (item.value / total) * 100;

                return (
                  <div key={item.name} className="group relative flex flex-col gap-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-foreground/80">{item.name}</span>
                      <div className="flex items-center gap-3">
                        <span className="font-semibold nums">{item.value}</span>
                        <span className="text-xs font-medium text-muted-foreground nums w-10 text-right">
                          {percentOfTotal.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="relative h-2 w-full overflow-hidden rounded-full bg-foreground/5 shadow-inner">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentOfMax}%` }}
                        transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: idx * 0.1 }}
                        className="absolute inset-y-0 left-0 rounded-full"
                        style={{
                          background: `linear-gradient(90deg, color-mix(in srgb, ${item.fill} 20%, transparent), ${item.fill})`,
                          boxShadow: `0 0 10px 0 color-mix(in srgb, ${item.fill} 40%, transparent)`,
                        }}
                      />
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </GlassPanel>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1fr]">
        {/* High-risk queue */}
        <GlassPanel className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold">High-risk queue</h3>
              <p className="text-xs text-muted-foreground">Claims requiring attention</p>
            </div>
            <Button asChild variant="ghost" size="sm" className="gap-1 text-xs">
              <Link href="/app/claims">
                View all <ArrowUpRight className="h-3 w-3" />
              </Link>
            </Button>
          </div>
          <div className="space-y-3">
            {highRiskClaims.map((c) => (
              <Link
                key={c.id}
                href={`/app/claims/${c.id}`}
                className="flex items-center gap-4 rounded-xl border border-border p-3 transition-colors hover:border-brand/30 hover:bg-accent/40"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm nums">{c.claimNumber}</span>
                    {c.prediction && (
                      <RiskBadge tier={c.prediction.riskTier} score={c.prediction.fraudProbability} />
                    )}
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{c.customer.name}</span>
                    <span className="text-border">·</span>
                    <span>{inr(c.claimAmount, { compact: true })}</span>
                    <span className="text-border">·</span>
                    <span>{fmtDate(c.incidentDate)}</span>
                  </div>
                </div>
                <div className="hidden sm:block">
                  <Sparkline
                    data={c.shap?.map((s) => Math.abs(s.contribution)) ?? []}
                    color={c.prediction?.riskTier === "high" ? "var(--risk-high)" : "var(--risk-elevated)"}
                    width={60}
                    height={28}
                  />
                </div>
              </Link>
            ))}
          </div>
        </GlassPanel>

        {/* SHAP drivers + agent feed */}
        <div className="space-y-6">
          {/* Top SHAP drivers */}
          <GlassPanel className="p-6">
            <div className="mb-4 flex items-center gap-2">
              <Brain className="h-4 w-4 text-brand" />
              <h3 className="text-sm font-semibold">Top SHAP drivers</h3>
              <span className="ml-auto text-[10px] text-muted-foreground">avg. impact across claims</span>
            </div>
            <div className="space-y-4">
              {(() => {
                // Aggregate SHAP contributions per raw feature across all claims,
                // then look up a readable label + description for each.
                const aggregated = claims
                  .filter((c) => c.shap && c.shap.length > 0)
                  .flatMap((c) => c.shap!)
                  .reduce((acc, s) => {
                    const key = s.feature;
                    if (!acc[key]) acc[key] = { feature: key, contribution: 0, absSum: 0, count: 0 };
                    acc[key].contribution += s.contribution;
                    acc[key].absSum += Math.abs(s.contribution);
                    acc[key].count += 1;
                    return acc;
                  }, {} as Record<string, { feature: string; contribution: number; absSum: number; count: number }>);

                return Object.values(aggregated)
                  .map(s => {
                    const info = humanizeFeature(s.feature);
                    return {
                      feature: s.feature,
                      label: info.label,
                      description: info.description,
                      contribution: s.contribution / s.count,
                      absSum: s.absSum / s.count,
                      count: s.count,
                    };
                  })
                  .sort((a, b) => b.absSum - a.absSum)
                  .slice(0, 5);
              })().map((s, i) => {
                const increases = s.contribution > 0;
                return (
                  <div key={`${s.feature}-${i}`} className="space-y-1.5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <span className="text-xs font-medium text-foreground/90">{s.label}</span>
                        <p className="text-[10px] text-muted-foreground/70 leading-snug mt-0.5">{s.description}</p>
                      </div>
                      <span className={`nums font-semibold text-xs shrink-0 ${increases ? "text-risk-high" : "text-risk-low"}`}>
                        {increases ? "↑" : "↓"} {Math.abs(s.contribution).toFixed(1)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className={`h-full rounded-full ${increases ? "bg-risk-high" : "bg-risk-low"}`}
                          style={{ width: `${Math.min(Math.abs(s.contribution) / 35 * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-[9px] text-muted-foreground/60 shrink-0 w-24 text-right">
                        {increases ? "Raises" : "Lowers"} fraud risk
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassPanel>
        </div>
      </div>
    </PageTransition>
  );
}

function num(n: number): string {
  return new Intl.NumberFormat("en-IN").format(n);
}

function KpiCard({
  label,
  value,
  change,
  icon,
  iconColor,
}: {
  label: string;
  value: React.ReactNode;
  change?: string;
  icon: React.ReactNode;
  iconColor: string;
}) {
  return (
    <GlassPanel className="p-5 transition-colors hover:border-brand/30">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-card/80 border border-border ${iconColor}`}>{icon}</div>
      </div>
      <div className="mt-3 font-heading text-2xl font-medium tracking-tight bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">{value}</div>
      {change && <p className="mt-1 text-xs text-muted-foreground/70">{change}</p>}
    </GlassPanel>
  );
}
