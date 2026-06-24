"use client";

import Hero from "@/components/ui/animated-shader-hero";
import { useRouter } from "next/navigation";

import Link from "next/link";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { RiskGauge } from "@/components/ui/risk-gauge";
import { AnimatedNumber, FadeIn, MotionStagger, MotionItem } from "@/components/ui/motion";
import { Pipeline } from "@/components/landing/pipeline";
import { SiteHeader, SiteFooter } from "@/components/landing/site-header";
import { DottedSurface } from "@/components/ui/dotted-surface";
import { GlassPanel, GradientBorderPanel, SectionHeading } from "@/components/ui/claimguard";
import {
  ArrowRight,
  Brain,
  GitBranch,
  Bot,
  ShieldCheck,
  FileText,
  Gauge,
  Sparkles,
  TrendingDown,
  Users,
  Search,
  CheckCircle2,
  AlertTriangle,
  FileWarning,
} from "lucide-react";

const heroShap = [
  { label: "High claim amount", value: 32 },
  { label: "No police report", value: 21 },
  { label: "Reporting delay", value: 17 },
  { label: "Previous claims", value: 15 },
];

const capabilities = [
  {
    icon: Brain,
    title: "Machine learning at the core",
    desc: "A gradient-boosted model — trained on TGAN-balanced data — scores every claim for fraud probability with calibrated confidence.",
    span: "lg:col-span-2",
  },
  {
    icon: GitBranch,
    title: "Explainable by design",
    desc: "SHAP surfaces the exact features driving each prediction, in plain language an investigator can act on.",
    span: "",
  },
  {
    icon: Bot,
    title: "Agentic reasoning",
    desc: "A team of specialized AI agents — Rule, History, SHAP, Report — orchestrated to investigate, not just predict.",
    span: "",
  },
  {
    icon: FileText,
    title: "Investigation reports, generated",
    desc: "Auto-produced summaries, risk analysis, rule violations, and recommended next steps. Exportable as PDF or HTML.",
    span: "lg:col-span-2",
  },
];

const agents = [
  { icon: Bot, name: "Orchestrator", role: "Coordinates the investigation across all agents." },
  { icon: ShieldCheck, name: "Rule Agent", role: "Checks claims against insurance rules & IRDAI guidelines." },
  { icon: Search, name: "History Agent", role: "Reviews the customer's prior claim patterns." },
  { icon: GitBranch, name: "SHAP Agent", role: "Interprets the model's feature contributions." },
  { icon: FileText, name: "Report Agent", role: "Synthesizes findings into a decision-ready report." },
];


export default function LandingPage() {
  const router = useRouter();

  const handlePrimaryClick = () => {
    router.push("/app/claims/new");
  };

  const handleSecondaryClick = () => {
    router.push("/login");
  };

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <DottedSurface className="fixed inset-0 -z-10" />
      <SiteHeader />

      {/* ============ HERO ============ */}
      <Hero
        trustBadge={{
          text: "AI-Powered Insurance Fraud Intelligence",
          icons: ["🛡️"]
        }}
        headline={{
          line1: "Protect Your Assets",
          line2: "Detect Fraud Instantly"
        }}
        subtitle="Leverage state-of-the-art machine learning and autonomous agents to investigate insurance claims with precision, speed, and absolute clarity."
        buttons={{
          primary: {
            text: "Submit a Claim",
            onClick: handlePrimaryClick
          },
          secondary: {
            text: "Investigator Login",
            onClick: handleSecondaryClick
          }
        }}
      />

      {/* ============ CAPABILITIES (bento) ============ */}
      <section id="capabilities" className="py-24">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
          <SectionHeading
            eyebrow="Capabilities"
            title="Everything an investigator needs, in one platform"
            description="From the first claim submission to the final decision, ClaimGuard orchestrates detection, explanation, and investigation — not just prediction."
            className="mb-12 max-w-3xl"
          />
          <div className="grid gap-5 lg:grid-cols-3">
            <MotionStagger className="contents" stagger={0.06}>
              {capabilities.map((c) => (
                <MotionItem key={c.title} className={c.span}>
                  <div className="group relative h-full overflow-hidden rounded-2xl border border-border bg-card p-6 transition-all duration-300 hover:border-brand/40 hover:shadow-[0_20px_50px_-30px_var(--brand)]">
                    <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand/10 text-brand transition-colors group-hover:bg-brand/15">
                      <c.icon className="h-5 w-5" strokeWidth={1.8} />
                    </div>
                    <h3 className="font-heading text-lg font-medium">{c.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{c.desc}</p>
                  </div>
                </MotionItem>
              ))}
            </MotionStagger>
          </div>
        </div>
      </section>

      {/* ============ PIPELINE ============ */}
      <section id="pipeline" className="border-y border-border bg-card/10 backdrop-blur-lg border-y border-brand/10 py-24">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
          <SectionHeading
            eyebrow="How it works"
            title="From claim submission to final decision"
            description="A complete pipeline that moves intelligently from raw data to a defensible, explainable decision."
            className="mb-14 max-w-3xl"
          />
          <Pipeline />
        </div>
      </section>

      {/* ============ AGENTS ============ */}
      <section id="agents" className="py-24">
        <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
          <SectionHeading
            eyebrow="AI Agents"
            title="A team of agents, not a single black box"
            description="Instead of one model doing everything, specialized agents each handle a part of the investigation — coordinated by an orchestrator."
            className="mb-12 max-w-3xl"
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {agents.map((a, i) => (
              <FadeIn key={a.name} delay={i * 0.06}>
                <GlassPanel className="h-full p-5">
                  <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl border border-brand/20 bg-brand/8 text-brand">
                    <a.icon className="h-5 w-5" strokeWidth={1.8} />
                  </div>
                  <h3 className="text-sm font-semibold">{a.name}</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{a.role}</p>
                </GlassPanel>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ============ PRINCIPLE ============ */}
      <section className="border-y border-border bg-card/10 backdrop-blur-lg border-y border-brand/10 py-24">
        <div className="mx-auto max-w-[1100px] px-4 sm:px-6">
          <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
            <div>
              <div className="mb-1.5 text-[11px] font-medium uppercase tracking-[0.2em] text-brand">The principle</div>
              <h2 className="font-heading text-3xl font-medium tracking-tight text-balance sm:text-4xl">
                The AI assists. The investigator decides.
              </h2>
              <p className="mt-4 text-muted-foreground text-pretty">
                ClaimGuard never automatically rejects a claim. It surfaces risk, explains it, and recommends next
                steps — so the human investigator stays in control of every decision.
              </p>
              <div className="mt-8 space-y-4">
                {[
                  { icon: AlertTriangle, color: "text-risk-high", title: "Detect", desc: "Score every claim for fraud probability with calibrated confidence." },
                  { icon: GitBranch, color: "text-brand", title: "Explain", desc: "Understand the precise features driving each prediction." },
                  { icon: FileWarning, color: "text-risk-elevated", title: "Investigate", desc: "Follow AI-recommended verification steps and rule checks." },
                  { icon: CheckCircle2, color: "text-risk-low", title: "Decide", desc: "Approve, reject, or request more — the call is always yours." },
                ].map((s) => (
                  <div key={s.title} className="flex gap-4">
                    <div className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-muted ${s.color}`}>
                      <s.icon className="h-4 w-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">{s.title}</h4>
                      <p className="mt-0.5 text-sm text-muted-foreground">{s.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <FadeIn delay={0.1}>
              <GradientBorderPanel className="bg-card">
                <div className="p-6">
                  <div className="mb-4 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    <Gauge className="h-3.5 w-3.5 text-brand" /> Investigation recommendation
                  </div>
                  <div className="flex items-center gap-5">
                    <RiskGauge value={87} tier="high" size="sm" showHalo={false} />
                    <div>
                      <p className="font-heading text-xl font-medium">Investigate further</p>
                      <p className="mt-1 text-sm text-muted-foreground">Confidence 93%</p>
                    </div>
                  </div>
                  <div className="mt-5 space-y-2 border-t border-border pt-4 text-sm">
                    {["Request original FIR", "Dispatch field investigator", "Pull vehicle telematics", "Cross-reference witness"].map((t) => (
                      <div key={t} className="flex items-center gap-2 text-muted-foreground">
                        <CheckCircle2 className="h-3.5 w-3.5 text-brand" /> {t}
                      </div>
                    ))}
                  </div>
                </div>
              </GradientBorderPanel>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ============ CTA ============ */}
      <section className="py-28">
        <div className="mx-auto max-w-[900px] px-4 text-center sm:px-6">
          <FadeIn>
            <div className="bg-spotlight relative overflow-hidden rounded-3xl border border-brand/20 bg-card/50 p-12 backdrop-blur-sm sm:p-16">
                            <div className="relative">
                <Users className="mx-auto mb-5 h-8 w-8 text-brand" />
                <h2 className="font-heading text-3xl font-medium tracking-tight text-balance sm:text-4xl">
                  Ready to investigate smarter?
                </h2>
                <p className="mx-auto mt-4 max-w-md text-muted-foreground">
                  Explore the full platform — dashboard, fraud analysis, AI-generated reports, and admin controls.
                </p>
                <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                  <Button asChild size="lg" className="gap-2 rounded-xl bg-brand text-primary-foreground hover:bg-brand/90">
                    <Link href="/app/dashboard">
                      Launch platform <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                  <Button asChild size="lg" variant="outline" className="rounded-xl">
                    <Link href="/app/claims/new">Submit a claim</Link>
                  </Button>
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
