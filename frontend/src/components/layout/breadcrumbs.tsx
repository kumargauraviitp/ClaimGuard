"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

const labels: Record<string, string> = {
  app: "Workspace",
  dashboard: "Dashboard",
  claims: "Claims",
  new: "New",
  analysis: "Fraud Analysis",
  investigation: "Investigation Report",
  analytics: "Analytics",
  admin: "Admin Panel",
  settings: "Settings",
  profile: "Profile",
  users: "Users & Roles",
  flags: "Feature Flags",
  audit: "Audit Log",
};

export function Breadcrumbs({ claimLabel }: { claimLabel?: string }) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const crumbs = segments.map((seg, i) => {
    const href = "/" + segments.slice(0, i + 1).join("/");
    const isLast = i === segments.length - 1;
    const label = claimLabel && isLast ? claimLabel : labels[seg] ?? seg.replace(/-/g, " ");
    return { href, label, isLast };
  });

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground">
      {crumbs.map((c, i) => (
        <React.Fragment key={c.href}>
          {i > 0 && <ChevronRight className="h-3.5 w-3.5 opacity-50" />}
          {c.isLast ? (
            <span className="font-medium capitalize text-foreground">{c.label}</span>
          ) : (
            <Link href={c.href} className="capitalize transition-colors hover:text-foreground">
              {c.label}
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
