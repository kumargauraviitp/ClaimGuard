"use client";

import * as React from "react";
import { motion } from "motion/react";
import { Database, Cpu, GitBranch, Bot, FileText, UserCheck } from "lucide-react";

const stages = [
  { icon: Database, label: "Data Collection", desc: "Customer, vehicle, policy & incident data" },
  { icon: Cpu, label: "ML Engine", desc: "GBM trained on TGAN-balanced data" },
  { icon: GitBranch, label: "Explainable AI", desc: "SHAP breaks down every prediction" },
  { icon: Bot, label: "AI Agents", desc: "Multi-agent reasoning & retrieval" },
  { icon: FileText, label: "Investigation Report", desc: "Auto-generated, exportable" },
  { icon: UserCheck, label: "Human Investigator", desc: "Always in control of the decision" },
];

export function Pipeline() {
  return (
    <div className="relative">
      {/* connecting line */}
      <div className="absolute left-0 right-0 top-7 hidden h-px bg-gradient-to-r from-transparent via-border to-transparent lg:block" />
      <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-6">
        {stages.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="relative flex flex-col items-center text-center"
          >
            <div className="relative mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-card">
              <div className="absolute inset-0 rounded-2xl bg-brand/5" />
              <s.icon className="relative h-6 w-6 text-brand" strokeWidth={1.8} />
              <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-background text-[10px] font-semibold text-muted-foreground ring-1 ring-border nums">
                {i + 1}
              </span>
            </div>
            <h4 className="text-sm font-semibold">{s.label}</h4>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{s.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
