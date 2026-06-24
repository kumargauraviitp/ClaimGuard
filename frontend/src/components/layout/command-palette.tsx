"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "@/components/ui/command";
import { quickNav } from "@/lib/nav";
import { useAppData } from "@/lib/hooks/use-app-data";
import { Search, ArrowRight, FolderSearch, Brain, FileText } from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();
  const { claims, disconnected } = useAppData();

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const go = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="group inline-flex h-9 items-center gap-2 rounded-xl border border-border bg-card/60 px-3 text-sm text-muted-foreground transition-colors hover:border-brand/40 hover:bg-accent/40"
      >
        <Search className="h-4 w-4" />
        <span className="hidden md:inline">Search claims, pages…</span>
        <kbd className="ml-1 hidden items-center gap-0.5 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground md:inline-flex">
          ⌘K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Search pages, claims, or actions…" />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>

          <CommandGroup heading="Navigation">
            {quickNav.map((item) => (
              <CommandItem key={item.href} value={`${item.label} ${item.description ?? ""}`} onSelect={() => go(item.href)}>
                <item.icon className="mr-2 h-4 w-4 text-muted-foreground" />
                <span>{item.label}</span>
                {item.description && <span className="ml-auto text-xs text-muted-foreground">{item.description}</span>}
              </CommandItem>
            ))}
          </CommandGroup>

          <CommandSeparator />

          <CommandGroup heading="Quick Actions">
            <CommandItem onSelect={() => go("/app/claims/new")}>
              <FolderSearch className="mr-2 h-4 w-4 text-muted-foreground" /> New claim
            </CommandItem>
            <CommandItem onSelect={() => go("/app/analysis")}>
              <Brain className="mr-2 h-4 w-4 text-muted-foreground" /> Run fraud analysis
            </CommandItem>
            <CommandItem onSelect={() => go("/app/investigation")}>
              <FileText className="mr-2 h-4 w-4 text-muted-foreground" /> Open latest investigation report
            </CommandItem>
          </CommandGroup>

          {!disconnected && claims.length > 0 && (
            <>
              <CommandSeparator />
              <CommandGroup heading="Claims">
                {claims.slice(0, 6).map((c) => (
                  <CommandItem
                    key={c.id}
                    value={`${c.claimNumber} ${c.customer.name} ${c.vehicle.make} ${c.vehicle.model}`}
                    onSelect={() => go(`/app/claims/${c.id}`)}
                  >
                    <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span className="font-medium nums">{c.claimNumber}</span>
                    <span className="mx-2 text-muted-foreground">·</span>
                    <span>{c.customer.name}</span>
                    <span className="ml-auto text-xs text-muted-foreground">
                      {c.prediction ? `${c.prediction.fraudProbability}% risk` : c.status}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </>
          )}
        </CommandList>
      </CommandDialog>
    </>
  );
}
