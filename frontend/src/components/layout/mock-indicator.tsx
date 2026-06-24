"use client";

import * as React from "react";
import { useSettings } from "@/lib/store";
import { Database, FlaskConical } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { LiveDot } from "@/components/ui/claimguard";

/**
 * Shows whether the workspace is running on mock/sample data or live data.
 * Always visible in the topbar; toggled from Admin → System → Mock Data.
 */
export function MockIndicator({ compact = false }: { compact?: boolean }) {
  const mockDataEnabled = useSettings((s) => s.mockDataEnabled);

  if (mockDataEnabled) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-2.5 py-1 text-[11px] font-medium text-brand",
              compact && "px-2",
            )}
          >
            <FlaskConical className="h-3 w-3" />
            {!compact && <span>Sample data</span>}
          </div>
        </TooltipTrigger>
        <TooltipContent>Workspace is running on sample data. Toggle off in Admin → System.</TooltipContent>
      </Tooltip>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border border-risk-low/30 bg-risk-low/10 px-2.5 py-1 text-[11px] font-medium text-risk-low",
            compact && "px-2",
          )}
        >
          <Database className="h-3 w-3" />
          {!compact && <span className="flex items-center gap-1.5">Live <LiveDot /></span>}
        </div>
      </TooltipTrigger>
      <TooltipContent>Connected to live data source.</TooltipContent>
    </Tooltip>
  );
}
