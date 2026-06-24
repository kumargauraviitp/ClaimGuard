"use client";

import * as React from "react";
import Link from "next/link";
import { useAppData } from "@/lib/hooks/use-app-data";
import { inr, fmtDate, relativeTime } from "@/lib/format";
import { RiskBadge, StatusBadge, EmptyState, PageHeader, PageTransition } from "@/components/ui/claimguard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Search, Plus, ArrowUpDown, Filter, CheckCircle2, Trash2, Loader2 } from "lucide-react";
import { useAuthStore } from "@/lib/authStore";
import apiClient from "@/lib/apiClient";
import type { Claim } from "@/lib/types";

type SortKey = "fraudProbability" | "claimAmount" | "incidentDate" | "createdAt";

export default function ClaimsPage() {
  const data = useAppData();
  const { user } = useAuthStore();
  const isAdmin = user?.roles?.some(r => r.toLowerCase() === "admin");
  const [search, setSearch] = React.useState("");
  const [sortKey, setSortKey] = React.useState<SortKey>("createdAt");
  const [sortAsc, setSortAsc] = React.useState(false);
  const [deleteTarget, setDeleteTarget] = React.useState<Claim | null>(null);
  const [deleting, setDeleting] = React.useState(false);

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await apiClient.delete(`/api/claims/${deleteTarget.id}`);
      window.location.reload();
    } catch (err) {
      console.error("Delete failed:", err);
      setDeleting(false);
      alert("Failed to delete claim. Please try again.");
    }
  };

  if (data.disconnected) {
    return (
      <PageTransition>
        <PageHeader title="Claims" description="All submitted claims" />
        <EmptyState
          icon={<Search className="h-6 w-6" />}
          title="No claims to display"
          description="Enable sample data or connect your data source."
          action={
            <Button asChild size="sm">
              <Link href="/app/admin">Open admin panel</Link>
            </Button>
          }
        />
      </PageTransition>
    );
  }

  const filtered = data.claims
    .filter((c) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        c.claimNumber.toLowerCase().includes(q) ||
        c.customer.name.toLowerCase().includes(q) ||
        c.vehicle.make.toLowerCase().includes(q) ||
        c.vehicle.model.toLowerCase().includes(q) ||
        c.status.includes(q)
      );
    })
    .sort((a, b) => {
      const dir = sortAsc ? 1 : -1;
      switch (sortKey) {
        case "fraudProbability":
          return ((a.prediction?.fraudProbability ?? 0) - (b.prediction?.fraudProbability ?? 0)) * dir;
        case "claimAmount":
          return (a.claimAmount - b.claimAmount) * dir;
        case "incidentDate":
          return (new Date(a.incidentDate).getTime() - new Date(b.incidentDate).getTime()) * dir;
        case "createdAt":
          return (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()) * dir;
        default:
          return 0;
      }
    });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Workspace"
        title="Claims"
        description={`${data.claims.length} claims total`}
        action={
          <Button asChild size="sm" className="gap-1.5 bg-brand text-primary-foreground hover:bg-brand/90">
            <Link href="/app/claims/new"><Plus className="h-4 w-4" /> New claim</Link>
          </Button>
        }
      />

      {/* Search + filters */}
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by claim number, customer, vehicle…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button variant="outline" size="sm" className="gap-1.5">
          <Filter className="h-3.5 w-3.5" /> Filters
        </Button>
        <Badge variant="secondary" className="text-[10px]">{filtered.length} results</Badge>
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[140px]">
                <button onClick={() => toggleSort("createdAt")} className="flex items-center gap-1 hover:text-foreground">
                  Claim <ArrowUpDown className="h-3 w-3" />
                </button>
              </TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Vehicle</TableHead>
              <TableHead className="text-right">
                <button onClick={() => toggleSort("claimAmount")} className="flex items-center gap-1 ml-auto hover:text-foreground">
                  Amount <ArrowUpDown className="h-3 w-3" />
                </button>
              </TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">
                <button onClick={() => toggleSort("fraudProbability")} className="flex items-center gap-1 ml-auto hover:text-foreground">
                  Risk <ArrowUpDown className="h-3 w-3" />
                </button>
              </TableHead>
              <TableHead className="text-right">Date</TableHead>
              {isAdmin && <TableHead className="text-right">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((c) => (
              <TableRow key={c.id} className="cursor-pointer hover:bg-accent/40">
                <TableCell>
                  <Link href={`/app/claims/${c.id}`} className="font-medium text-sm hover:underline nums flex items-center gap-1.5">
                    {c.claimNumber}
                    {c.status === "investigating" && <span title="Reviewed"><CheckCircle2 className="h-3.5 w-3.5 text-[#8b5cf6]" /></span>}
                  </Link>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{c.customer.name}</div>
                  <div className="text-xs text-muted-foreground">{c.customer.city}</div>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{c.vehicle.make} {c.vehicle.model}</div>
                  <div className="text-xs text-muted-foreground">{c.vehicle.registrationNumber}</div>
                </TableCell>
                <TableCell className="text-right nums font-medium">{inr(c.claimAmount, { compact: true })}</TableCell>
                <TableCell><StatusBadge status={c.status} /></TableCell>
                <TableCell className="text-right">
                  {c.prediction ? (
                    <div className="flex items-center justify-end gap-2">
                      <span className="nums text-xs text-muted-foreground">{c.prediction.fraudProbability}%</span>
                      <RiskBadge tier={c.prediction.riskTier} />
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground">Pending</span>
                  )}
                </TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">
                  {new Date(c.incidentDate).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })}
                </TableCell>
                {isAdmin && (
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="icon-sm"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setDeleteTarget(c);
                      }}
                      title="Delete claim"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => { if (!deleting) setDeleteTarget(open ? deleteTarget : null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete claim?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete claim <span className="font-medium text-foreground nums">{deleteTarget?.claimNumber}</span> and all its associated data (predictions, documents, investigation records). This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={(e) => { e.preventDefault(); confirmDelete(); }}
              disabled={deleting}
            >
              {deleting ? <><Loader2 className="h-4 w-4 animate-spin" /> Deleting…</> : "Delete claim"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageTransition>
  );
}
