"use client";

import * as React from "react";
import { ResponsiveContainer } from "recharts";

// A thin wrapper so Recharts always has a ResponsiveContainer.
export function ChartContainer({ children, className, height = 300 }: { children: React.ReactNode; className?: string; height?: number }) {
  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height={height} minWidth={0}>
        {children as React.JSX.Element}
      </ResponsiveContainer>
    </div>
  );
}
