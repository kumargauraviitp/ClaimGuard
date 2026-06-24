"use client";

import * as React from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

// Smooth page-level enter animation. Respects reduced motion via CSS.
export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function PageHeader({
  title,
  description,
  eyebrow,
  action,
  className,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  eyebrow?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div>
        {eyebrow && (
          <div className="mb-1.5 text-[11px] font-medium uppercase tracking-[0.2em] text-brand">{eyebrow}</div>
        )}
        <h1 className="font-heading text-2xl font-medium tracking-tight text-balance sm:text-[1.75rem] bg-gradient-to-br from-violet-200 via-purple-300 to-fuchsia-400 bg-clip-text text-transparent pb-1">{title}</h1>
        {description && <p className="mt-1.5 max-w-2xl text-sm text-violet-200/70 text-pretty">{description}</p>}
      </div>
      {action && <div className="flex shrink-0 items-center gap-2">{action}</div>}
    </div>
  );
}
