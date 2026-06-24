"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShieldAlert, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 text-center">
      <div className="bg-grid bg-grid-fade pointer-events-none absolute inset-0" aria-hidden />
      <div className="bg-spotlight pointer-events-none absolute inset-0" aria-hidden />

      <div className="relative">
        <span className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand text-primary-foreground">
          <ShieldAlert className="h-7 w-7" strokeWidth={2.2} />
        </span>
        <p className="font-heading text-7xl font-medium text-brand nums">404</p>
        <h1 className="mt-3 font-heading text-2xl font-medium tracking-tight">This claim doesn't exist</h1>
        <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
          The page you're looking for may have been moved, deleted, or never filed.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Button asChild variant="outline" className="gap-1.5">
            <Link href="/"><ArrowLeft className="h-4 w-4" /> Home</Link>
          </Button>
          <Button asChild className="bg-brand text-primary-foreground hover:bg-brand/90">
            <Link href="/app/dashboard">Go to dashboard</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
