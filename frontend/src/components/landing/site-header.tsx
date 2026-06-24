"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShieldAlert, ArrowRight } from "lucide-react";
import { ModeToggle } from "@/components/layout/mode-toggle";
import { cn } from "@/lib/utils";

const links = [
  { href: "#capabilities", label: "Capabilities" },
  { href: "#pipeline", label: "How it works" },
  { href: "#agents", label: "AI Agents" },
  { href: "#metrics", label: "Performance" },
];

export function SiteHeader() {
  const [scrolled, setScrolled] = React.useState(false);
  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled ? "border-b border-border bg-background/70 backdrop-blur-xl" : "bg-transparent",
      )}
    >
      <div className="mx-auto flex h-16 max-w-[1200px] items-center gap-6 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-primary-foreground">
            <ShieldAlert className="h-5 w-5" strokeWidth={2.2} />
          </span>
          <span className="flex flex-col leading-none">
            <span className="font-heading text-lg font-medium tracking-tight">ClaimGuard</span>
          </span>
        </Link>

        <nav className="ml-4 hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <ModeToggle />
          <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
            <Link href="/app/dashboard">Sign in</Link>
          </Button>
          <Button asChild size="sm" className="gap-1.5 rounded-xl bg-brand text-primary-foreground hover:bg-brand/90">
            <Link href="/app/dashboard">
              Launch platform <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto grid max-w-[1200px] gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
        <div>
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-primary-foreground">
              <ShieldAlert className="h-4 w-4" strokeWidth={2.2} />
            </span>
            <span className="font-heading text-lg font-medium">ClaimGuard</span>
          </Link>
          <p className="mt-4 max-w-xs text-sm text-muted-foreground">
            The AI-powered insurance fraud investigation platform. Detect, explain, and decide — with the human
            investigator always in control.
          </p>
        </div>
        <FooterCol
          title="Platform"
          links={[
            { href: "/app/dashboard", label: "Dashboard" },
            { href: "/app/claims", label: "Claims" },
            { href: "/app/analysis", label: "Fraud Analysis" },
            { href: "/app/investigation", label: "Investigation Report" },
          ]}
        />
        <FooterCol
          title="System"
          links={[
            { href: "/app/analytics", label: "Analytics" },
            { href: "/app/admin", label: "Admin Panel" },
            { href: "/app/settings", label: "Settings" },
            { href: "/app/profile", label: "Profile" },
          ]}
        />
        <FooterCol
          title="Resources"
          links={[
            { href: "#capabilities", label: "Capabilities" },
            { href: "#pipeline", label: "How it works" },
            { href: "#agents", label: "AI Agents" },
            { href: "#metrics", label: "Performance" },
          ]}
        />
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-[1200px] flex-col items-center justify-between gap-2 px-4 py-5 text-xs text-muted-foreground sm:flex-row sm:px-6">
          <p>© 2026 ClaimGuard Fraud Intelligence. Built for enterprise investigators.</p>
          <p className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-risk-low" />
            All systems operational
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: { href: string; label: string }[] }) {
  return (
    <div>
      <h4 className="text-sm font-semibold">{title}</h4>
      <ul className="mt-4 space-y-2.5">
        {links.map((l) => (
          <li key={l.label}>
            <Link href={l.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
