"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { navGroups } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { ChevronLeft, ShieldAlert } from "lucide-react";
import { MockIndicator } from "@/components/layout/mock-indicator";
import { useSettings } from "@/lib/store";
import { useShell } from "@/components/layout/sidebar-state";
import { useAppData } from "@/lib/hooks/use-app-data";
import { useAuthStore } from "@/lib/authStore";

export function Brand({ collapsed }: { collapsed?: boolean }) {
  return (
    <Link href="/" className="group flex items-center gap-2.5">
      <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand text-primary-foreground shadow-[0_8px_24px_-8px_var(--brand)]">
        <ShieldAlert className="h-5 w-5" strokeWidth={2.2} />
        <span className="absolute inset-0 rounded-xl ring-1 ring-inset ring-white/15" />
      </span>
      {!collapsed && (
        <span className="flex flex-col leading-none">
          <span className="font-heading text-[1.05rem] font-medium tracking-tight">ClaimGuard</span>
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Fraud Intelligence</span>
        </span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const mockDataEnabled = useSettings((s) => s.mockDataEnabled);
  const collapsed = useShell((s) => s.sidebarCollapsed);
  const toggleSidebar = useShell((s) => s.toggleSidebar);
  const { kpis } = useAppData();
  const { user } = useAuthStore();
  const userRoles = user?.roles?.map(r => r.toLowerCase()) || [];

  const filteredNavGroups = React.useMemo(() => {
    return navGroups.map(group => {
      const filteredItems = group.items.filter(item => {
        if (!item.roles) return true;
        return item.roles.some(role => userRoles.includes(role));
      });
      return { ...group, items: filteredItems };
    }).filter(group => group.items.length > 0);
  }, [userRoles]);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-border/50 lg:flex",
        "bg-sidebar/95 backdrop-blur-xl shadow-[4px_0_24px_-8px_color-mix(in_srgb,var(--foreground)_15%,transparent)] z-40",
        "transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]",
        collapsed ? "w-[78px]" : "w-[260px]",
      )}
    >
      <div className={cn("flex h-16 items-center border-b border-border/50 px-4", collapsed && "justify-center px-0")}>
        <Brand collapsed={collapsed} />
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {filteredNavGroups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground/70">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = pathname === item.href || (item.href !== "/app/dashboard" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                        collapsed && "justify-center px-0",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                      )}
                    >
                      {active && <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-brand" />}
                      <Icon className={cn("h-[1.15rem] w-[1.15rem] shrink-0", active && "text-brand")} strokeWidth={2} />
                      {!collapsed && (
                        <>
                          <span className="truncate">{item.label}</span>
                          {(item.badge || (item.label === "Claims" && kpis?.openInvestigations)) && (
                            <span className="ml-auto rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground nums">
                              {item.badge || kpis?.openInvestigations}
                            </span>
                          )}
                        </>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        {!collapsed && (
          <div className="mb-2 flex items-center justify-between px-1">
            <MockIndicator compact={false} />
            <button
              onClick={toggleSidebar}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          </div>
        )}
        {collapsed && (
          <button
            onClick={toggleSidebar}
            className="mx-auto flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
            aria-label="Expand sidebar"
          >
            <ChevronLeft className="h-4 w-4 rotate-180" />
          </button>
        )}
        {collapsed && mockDataEnabled && (
          <div className="mt-2 flex justify-center">
            <MockIndicator compact />
          </div>
        )}
      </div>
    </aside>
  );
}
