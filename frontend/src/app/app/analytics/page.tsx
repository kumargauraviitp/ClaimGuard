"use client";

import { useAppData } from "@/lib/hooks/use-app-data";
import { pct, compactNum } from "@/lib/format";
import { AnimatedNumber, FadeIn, MotionStagger, MotionItem } from "@/components/ui/motion";
import { EmptyState, GlassPanel, PageHeader, PageTransition, GradientBorderPanel } from "@/components/ui/claimguard";
import { ChartContainer } from "@/components/ui/chart-container";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, BarChart, Bar,
  LineChart, Line, Legend,
} from "recharts";
import { BarChart3, Gauge, Activity, MapPin } from "lucide-react";

export default function AnalyticsPage() {
  const data = useAppData();

  if (data.disconnected) {
    return (
      <PageTransition>
        <PageHeader title="Analytics" description="Trends & model performance" />
        <EmptyState icon={<BarChart3 className="h-6 w-6" />} title="No analytics data" description="Enable sample data to view analytics." action={<Button asChild size="sm"><Link href="/app/admin">Open admin</Link></Button>} />
      </PageTransition>
    );
  }

  const { fraudTrend, fraudDistribution, predictionHistory, investigationStatus, regionRisk, model } = data;

  return (
    <PageTransition>
      <PageHeader eyebrow="Intelligence" title="Analytics" description="Fraud trends, distributions & model performance" />

      {/* KPI strip */}
      <MotionStagger className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" stagger={0.04}>
        <MotionItem><KpiCard label="Model accuracy" value={<AnimatedNumber value={model.accuracy * 100} format={(n) => `${n.toFixed(1)}%`} />} icon={<Gauge className="h-4 w-4" />} color="text-risk-low" /></MotionItem>
        <MotionItem><KpiCard label="AUC score" value={<AnimatedNumber value={model.auc} format={(n) => n.toFixed(3)} />} icon={<Activity className="h-4 w-4" />} color="text-brand" /></MotionItem>
        <MotionItem><KpiCard label="False positive rate" value={<AnimatedNumber value={model.falsePositiveRate * 100} format={(n) => `${n.toFixed(1)}%`} />} icon={<BarChart3 className="h-4 w-4" />} color="text-risk-high" /></MotionItem>
        <MotionItem><KpiCard label="Drift score" value={<AnimatedNumber value={model.driftScore} format={(n) => n.toFixed(2)} />} icon={<Gauge className="h-4 w-4" />} color={model.driftScore > 0.15 ? "text-risk-elevated" : "text-risk-low"} /></MotionItem>
      </MotionStagger>

      <div className="grid gap-6 lg:grid-cols-2 mb-6">
        {/* Fraud rate trend */}
        <GlassPanel className="p-6">
          <h3 className="text-sm font-semibold mb-1">Fraud rate & claim volume</h3>
          <p className="text-xs text-muted-foreground mb-4">6-month trend</p>
          <ChartContainer height={260}>
            <AreaChart data={fraudTrend} margin={{ left: -20, right: 5 }}>
              <defs>
                <linearGradient id="an1" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.3} /><stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} domain={[0, "auto"]} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v: any, n: any) => [n === "fraudRate" ? `${(Number(v) * 100).toFixed(1)}%` : v, n === "fraudRate" ? "Fraud rate" : "Volume"]} />
              <Area type="monotone" dataKey="fraudRate" stroke="var(--chart-1)" fill="url(#an1)" strokeWidth={2} />
            </AreaChart>
          </ChartContainer>
        </GlassPanel>

        {/* Fraud distribution pie */}
        <GlassPanel className="p-6">
          <h3 className="text-sm font-semibold mb-1">Fraud by claim type</h3>
          <p className="text-xs text-muted-foreground mb-4">Distribution of detected fraud</p>
          <ChartContainer height={260}>
            <PieChart>
              <Pie data={fraudDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={3}>
                {fraudDistribution.map((e, i) => <Cell key={i} fill={e.fill} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
            </PieChart>
          </ChartContainer>
        </GlassPanel>
      </div>

      {/* Prediction history stacked */}
      <GlassPanel className="p-6 mb-6">
        <h3 className="text-sm font-semibold mb-1">Prediction history by risk tier</h3>
        <p className="text-xs text-muted-foreground mb-4">Weekly distribution of model predictions</p>
        <ChartContainer height={280}>
          <BarChart data={predictionHistory} margin={{ left: -20, right: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
            <XAxis dataKey="label" tick={{ fontSize: 12, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)", opacity: 0.3 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
            <Bar dataKey="high" stackId="a" fill="var(--risk-high)" radius={[0, 0, 0, 0]} />
            <Bar dataKey="elevated" stackId="a" fill="var(--risk-elevated)" />
            <Bar dataKey="moderate" stackId="a" fill="var(--risk-moderate)" />
            <Bar dataKey="low" stackId="a" fill="var(--risk-low)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </GlassPanel>

      <div className="grid gap-6 lg:grid-cols-2 mb-6">
        {/* Investigation status */}
        <GlassPanel className="p-6">
          <h3 className="text-sm font-semibold mb-1">Investigation status</h3>
          <p className="text-xs text-muted-foreground mb-4">Current pipeline breakdown</p>
          <ChartContainer height={240}>
            <PieChart>
              <Pie data={investigationStatus} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} paddingAngle={2}>
                {investigationStatus.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ChartContainer>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {investigationStatus.map((s) => (
              <div key={s.name} className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                <span className="text-muted-foreground">{s.name}</span>
                <span className="nums ml-auto font-medium">{s.value}</span>
              </div>
            ))}
          </div>
        </GlassPanel>

        {/* High-risk regions */}
        <GlassPanel className="p-6">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="h-4 w-4 text-brand" />
            <h3 className="text-sm font-semibold">Fraud rate by region</h3>
          </div>
          <p className="text-xs text-muted-foreground mb-4">Geographic risk distribution</p>
          <div className="space-y-4">
            {regionRisk.map((r) => (
              <div key={r.region}>
                <div className="flex items-center justify-between text-sm mb-1.5">
                  <span className="font-medium">{r.region}</span>
                  <span className="text-muted-foreground nums">{pct(r.fraudRate)} · {compactNum(r.claims)} claims</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full ${r.riskTier === "high" ? "bg-risk-high" : r.riskTier === "elevated" ? "bg-risk-elevated" : "bg-risk-moderate"}`}
                    style={{ width: `${Math.min(r.fraudRate * 100 * 5, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </GlassPanel>
      </div>

      {/* Model performance detail */}
      <GradientBorderPanel className="bg-card">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2"><Gauge className="h-4 w-4 text-brand" /><h3 className="text-sm font-semibold">Model performance</h3></div>
            <div className="flex items-center gap-2"><Badge variant="secondary" className="text-[10px]">{model.version}</Badge><Badge variant={model.driftScore > 0.15 ? "destructive" : "secondary"} className="text-[10px]">{model.driftScore > 0.15 ? "Drift alert" : "Healthy"}</Badge></div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {[
              { label: "Accuracy", value: `${(model.accuracy * 100).toFixed(1)}%` },
              { label: "Precision", value: `${(model.precision * 100).toFixed(1)}%` },
              { label: "Recall", value: `${(model.recall * 100).toFixed(1)}%` },
              { label: "F1 Score", value: model.f1.toFixed(3) },
              { label: "AUC", value: model.auc.toFixed(3) },
              { label: "FPR", value: `${(model.falsePositiveRate * 100).toFixed(1)}%` },
            ].map((m) => (
              <FadeIn key={m.label}>
                <div className="rounded-xl bg-muted p-4 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{m.label}</p>
                  <p className="font-heading text-xl font-medium mt-1 nums">{m.value}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </GradientBorderPanel>
    </PageTransition>
  );
}

const tooltipStyle = { background: "var(--card)", border: "1px solid var(--border)", borderRadius: "12px", fontSize: 12, color: "var(--foreground)" } as const;

function KpiCard({ label, value, icon, color }: { label: string; value: React.ReactNode; icon: React.ReactNode; color: string }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-center justify-between"><p className="text-xs font-medium text-muted-foreground">{label}</p><div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-muted ${color}`}>{icon}</div></div>
      <div className="mt-3 font-heading text-2xl font-medium tracking-tight">{value}</div>
    </div>
  );
}
