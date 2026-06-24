"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ModeToggle } from "@/components/layout/mode-toggle";
import { CommandPalette } from "@/components/layout/command-palette";
import { MobileNav } from "@/components/layout/mobile-nav";
import { MockIndicator } from "@/components/layout/mock-indicator";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Bell, Settings, UserCircle, LogOut, ShieldCheck, ChevronLeft, Plus } from "lucide-react";
import { useAppData } from "@/lib/hooks/use-app-data";
import { useAuthStore } from "@/lib/authStore";
import { relativeTime } from "@/lib/format";

const notifications = [
  { id: "n1", title: "High-risk claim flagged", body: "CLM-2026-4821 · 94% fraud probability", time: "2026-06-20T09:13:00", severity: "high" as const },
  { id: "n2", title: "Model drift crossed threshold", body: "gbm-tgan-v4.2 · drift 0.19", time: "2026-06-19T22:10:00", severity: "warning" as const },
  { id: "n3", title: "Investigation report ready", body: "CLM-2026-4802 · theft", time: "2026-06-19T11:05:00", severity: "info" as const },
  { id: "n4", title: "3 claims reassigned to you", body: "By Priya Raman", time: "2026-06-19T15:40:00", severity: "info" as const },
];

export function Topbar({ backHref }: { backHref?: string }) {
  const router = useRouter();
  const { disconnected } = useAppData();
  const { user, clearAuth } = useAuthStore();

  const handleSignOut = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b border-border/50 bg-background/80 px-4 backdrop-blur-xl shadow-[0_4px_24px_-8px_color-mix(in_srgb,var(--foreground)_15%,transparent)] sm:px-6">
      <MobileNav />

      <Link
        href={backHref ?? "/"}
        className="hidden items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground lg:flex"
      >
        <ChevronLeft className="h-4 w-4" />
        <span className="font-heading text-base text-foreground">ClaimGuard</span>
      </Link>

      <div className="hidden items-center md:flex">
        <Breadcrumbs />
      </div>

      <div className="ml-auto flex items-center gap-2">
        <div className="hidden sm:block">
          <MockIndicator compact />
        </div>

        <CommandPalette />

        <Button asChild size="sm" className="hidden h-9 rounded-xl bg-brand text-primary-foreground hover:bg-brand/90 sm:inline-flex">
          <Link href="/app/claims/new">
            <Plus className="mr-1 h-4 w-4" /> New Claim
          </Link>
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative h-9 w-9 rounded-xl" aria-label="Notifications">
              <Bell className="h-[1.15rem] w-[1.15rem]" />
              <span className="absolute right-1.5 top-1.5 flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-70" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-brand" />
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 p-0">
            <div className="flex items-center justify-between border-b px-3 py-2.5">
              <span className="text-sm font-semibold">Notifications</span>
              <Badge variant="secondary" className="text-[10px]">4 new</Badge>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.map((n) => (
                <button
                  key={n.id}
                  className="flex w-full gap-3 border-b px-3 py-3 text-left transition-colors last:border-0 hover:bg-accent/50"
                >
                  <span
                    className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${n.severity === "high" ? "bg-risk-high" : n.severity === "warning" ? "bg-risk-moderate" : "bg-chart-4"
                      }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium leading-tight">{n.title}</p>
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">{n.body}</p>
                    <p className="mt-1 text-[10px] text-muted-foreground/70">{relativeTime(n.time)}</p>
                  </div>
                </button>
              ))}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <ModeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-xl p-0.5 pl-1 transition-colors hover:bg-accent/50" aria-label="Account">
              <Avatar className="h-8 w-8 border border-border">
                <AvatarFallback className="bg-brand/15 text-xs font-semibold text-brand">
                  {user?.full_name?.charAt(0).toUpperCase() || "U"}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{user?.full_name || "User"}</span>
                <span className="text-xs font-normal text-muted-foreground">{user?.email || "user@example.com"}</span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push("/app/profile")}>
              <UserCircle className="mr-2 h-4 w-4" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/app/settings")}>
              <Settings className="mr-2 h-4 w-4" /> Settings
            </DropdownMenuItem>
            {user?.roles?.includes("Admin") && (
              <DropdownMenuItem onClick={() => router.push("/app/admin")}>
                <ShieldCheck className="mr-2 h-4 w-4" /> Admin Panel
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut} className="text-risk-high focus:text-risk-high">
              <LogOut className="mr-2 h-4 w-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
