"use client";

import * as React from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { MockDataBanner } from "@/components/layout/mock-data-banner";
import { DottedSurface } from "@/components/ui/dotted-surface";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-background text-foreground">
      <DottedSurface className="fixed inset-0 -z-10 opacity-70" />
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col z-0">
        <Topbar />
        <MockDataBanner />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-[1400px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
