"use client";

import * as React from "react";
import { useSettings } from "@/lib/store";
import { FlaskConical, X, Settings2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

/**
 * Dismissible banner shown at the top of the workspace when sample data is on,
 * to make the demo/mock state unmistakably clear.
 */
export function MockDataBanner() {
  const mockDataEnabled = useSettings((s) => s.mockDataEnabled);
  const dismissed = useSettings((s) => s.mockDataNoticeDismissed);
  const dismiss = useSettings((s) => s.dismissMockNotice);

  if (!mockDataEnabled || dismissed) return null;

  return (
    <div className="border-b border-brand/20 bg-brand/8 px-4 py-2 sm:px-6">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-2 text-xs">
        <FlaskConical className="h-3.5 w-3.5 shrink-0 text-brand" />
        <span className="text-foreground/80">
          <span className="font-medium text-brand">Sample data mode.</span> All claims, predictions, and
          reports shown are illustrative. Connect your data source in Admin → System.
        </span>
        <div className="ml-auto flex items-center gap-1">
          <Button asChild variant="ghost" size="sm" className="h-7 gap-1.5 px-2 text-xs">
            <Link href="/app/admin">
              <Settings2 className="h-3 w-3" /> Configure
            </Link>
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={dismiss} aria-label="Dismiss">
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
