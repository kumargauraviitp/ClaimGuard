"use client";

import * as React from "react";
import { useAppData } from "@/lib/hooks/use-app-data";
import { useSettings } from "@/lib/store";
import { PageTransition, PageHeader, GradientBorderPanel } from "@/components/ui/claimguard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { relativeTime, fmtDateTime } from "@/lib/format";
import {
  ShieldCheck, Database, FlaskConical, Users, ScrollText, Flag,
  Activity, Cpu, Server, CheckCircle2, AlertTriangle,
} from "lucide-react";

export default function AdminPage() {
  return (
    <PageTransition>
      <PageHeader eyebrow="System" title="Admin Panel" description="System controls, feature flags, users & audit" />

      <Tabs defaultValue="system">
        <TabsList className="mb-6 flex h-10 flex-wrap gap-1 rounded-xl bg-muted/50 p-1">
          <TabsTrigger value="system" className="gap-1.5"><Database className="h-3.5 w-3.5" /> System</TabsTrigger>
          <TabsTrigger value="flags" className="gap-1.5"><Flag className="h-3.5 w-3.5" /> Feature Flags</TabsTrigger>
          <TabsTrigger value="users" className="gap-1.5"><Users className="h-3.5 w-3.5" /> Users & Roles</TabsTrigger>
          <TabsTrigger value="audit" className="gap-1.5"><ScrollText className="h-3.5 w-3.5" /> Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="system"><SystemTab /></TabsContent>
        <TabsContent value="flags"><FlagsTab /></TabsContent>
        <TabsContent value="users"><UsersTab /></TabsContent>
        <TabsContent value="audit"><AuditTab /></TabsContent>
      </Tabs>
    </PageTransition>
  );
}

/* ============ SYSTEM ============ */
function SystemTab() {
  const { mockDataEnabled, setMockData } = useSettings();
  const data = useAppData();

  return (
    <div className="space-y-6">
      {/* Mock data toggle — primary */}
      <GradientBorderPanel className="bg-card">
        <div className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex gap-4">
              <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${mockDataEnabled ? "bg-brand/15 text-brand" : "bg-risk-low/15 text-risk-low"}`}>
                {mockDataEnabled ? <FlaskConical className="h-6 w-6" /> : <Database className="h-6 w-6" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-semibold">Sample Data Mode</h3>
                  <Badge variant={mockDataEnabled ? "secondary" : "outline"} className={mockDataEnabled ? "bg-brand/15 text-brand border-brand/25" : "bg-risk-low/15 text-risk-low border-risk-low/25"}>
                    {mockDataEnabled ? "ON" : "OFF"}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground max-w-lg">
                  When enabled, the entire workspace runs on rich illustrative data — claims, predictions, SHAP explanations, agent outputs, and analytics.
                  Turn it off to see the empty/connect-your-data states, ready for your live backend.
                </p>
              </div>
            </div>
            <Switch
              checked={mockDataEnabled}
              onCheckedChange={(v) => { setMockData(v); toast.success(`Sample data ${v ? "enabled" : "disabled"}`); }}
              className="scale-125"
            />
          </div>
          {!mockDataEnabled && (
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-risk-low/25 bg-risk-low/5 p-3 text-sm text-muted-foreground">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-risk-low" />
              <span>Workspace is now showing empty states. All pages are wired to display proper "no data" / "connect your data source" UI until a live backend is connected.</span>
            </div>
          )}
        </div>
      </GradientBorderPanel>

      {/* System health */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <HealthCard icon={<Server className="h-4 w-4" />} label="API Status" value="Operational" status="ok" />
        <HealthCard icon={<Cpu className="h-4 w-4" />} label="ML Model" value={data.model.version} status="ok" />
        <HealthCard icon={<Database className="h-4 w-4" />} label="Database" value="Connected" status="ok" />
        <HealthCard icon={<Activity className="h-4 w-4" />} label="Model Drift" value={`${data.model.driftScore.toFixed(2)} score`} status={data.model.driftScore > 0.15 ? "warn" : "ok"} />
      </div>

      {/* Environment */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h3 className="text-sm font-semibold mb-4">Environment</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <EnvRow label="Frontend" value="Next.js 16.2.9" />
          <EnvRow label="ML Backend" value="FastAPI (pending)" />
          <EnvRow label="Database" value="PostgreSQL / Supabase" />
          <EnvRow label="ML Framework" value="XGBoost + TGAN" />
          <EnvRow label="AI Agents" value="LangGraph + OpenAI" />
          <EnvRow label="Explainability" value="SHAP" />
        </div>
      </div>
    </div>
  );
}

function HealthCard({ icon, label, value, status }: { icon: React.ReactNode; label: string; value: string; status: "ok" | "warn" | "err" }) {
  const color = status === "ok" ? "text-risk-low bg-risk-low/10" : status === "warn" ? "text-risk-elevated bg-risk-elevated/10" : "text-risk-high bg-risk-high/10";
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">{label}</p>
        <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${color}`}>{icon}</div>
      </div>
      <p className="mt-2 text-sm font-medium">{value}</p>
      <div className="mt-2 flex items-center gap-1.5 text-[11px]">
        <span className={`h-1.5 w-1.5 rounded-full ${status === "ok" ? "bg-risk-low" : status === "warn" ? "bg-risk-elevated" : "bg-risk-high"}`} />
        <span className={status === "ok" ? "text-risk-low" : status === "warn" ? "text-risk-elevated" : "text-risk-high"}>
          {status === "ok" ? "Healthy" : status === "warn" ? "Attention" : "Error"}
        </span>
      </div>
    </div>
  );
}

function EnvRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-muted/40 px-3 py-2.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-medium nums">{value}</span>
    </div>
  );
}

/* ============ FEATURE FLAGS ============ */
function FlagsTab() {
  const data = useAppData();
  const toggleFlag = useSettings((s) => s.toggleFlag);
  const flags = useSettings((s) => s.flags);

  const categories = ["intelligence", "workflow", "integrations", "experimental"] as const;

  return (
    <div className="space-y-6">
      {categories.map((cat) => {
        const catFlags = data.featureFlags.filter((f) => f.category === cat);
        if (catFlags.length === 0) return null;
        return (
          <div key={cat}>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground capitalize">{cat}</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {catFlags.map((f) => {
                const enabled = flags[f.key] ?? f.enabled;
                return (
                  <div key={f.key} className="flex items-start justify-between gap-3 rounded-2xl border border-border bg-card p-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{f.label}</p>
                        {f.category === "experimental" && <Badge variant="outline" className="text-[9px] py-0">BETA</Badge>}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{f.description}</p>
                    </div>
                    <Switch checked={enabled} onCheckedChange={(v) => { toggleFlag(f.key, v); toast.success(`${f.label} ${v ? "enabled" : "disabled"}`); }} />
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ============ USERS ============ */
function UsersTab() {
  const data = useAppData();
  if (data.disconnected) {
    return <div className="py-20 text-center text-sm text-muted-foreground">No user data.</div>;
  }
  return (
    <div className="rounded-2xl border border-border bg-card">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div><h3 className="text-sm font-semibold">Team members</h3><p className="text-xs text-muted-foreground">{data.users.length} users</p></div>
        <Button size="sm" className="bg-brand text-primary-foreground hover:bg-brand/90"><Users className="h-3.5 w-3.5" /> Invite user</Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>User</TableHead>
            <TableHead>Role</TableHead>
            <TableHead>Department</TableHead>
            <TableHead className="text-right">Cases</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last active</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.users.map((u) => {
            const initials = u.name.split(" ").map((n) => n[0]).join("").slice(0, 2);
            return (
              <TableRow key={u.id} className="hover:bg-accent/40">
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8"><AvatarFallback className="bg-brand/15 text-[11px] font-semibold text-brand">{initials}</AvatarFallback></Avatar>
                    <div><p className="text-sm font-medium">{u.name}</p><p className="text-xs text-muted-foreground">{u.email}</p></div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="capitalize">{u.role}</Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">{u.department}</TableCell>
                <TableCell className="text-right nums text-sm">{u.casesAssigned} / {u.casesResolved}</TableCell>
                <TableCell>
                  <span className={`inline-flex items-center gap-1.5 text-xs ${u.status === "active" ? "text-risk-low" : u.status === "invited" ? "text-risk-moderate" : "text-risk-high"}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${u.status === "active" ? "bg-risk-low" : u.status === "invited" ? "bg-risk-moderate" : "bg-risk-high"}`} />
                    <span className="capitalize">{u.status}</span>
                  </span>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">{relativeTime(u.lastActive)}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

/* ============ AUDIT LOG ============ */
function AuditTab() {
  const data = useAppData();
  if (data.disconnected) {
    return <div className="py-20 text-center text-sm text-muted-foreground">No audit data.</div>;
  }
  return (
    <div className="rounded-2xl border border-border bg-card">
      <div className="p-4 border-b border-border">
        <h3 className="text-sm font-semibold">System activity log</h3>
        <p className="text-xs text-muted-foreground">{data.auditLog.length} entries</p>
      </div>
      <div className="divide-y divide-border">
        {data.auditLog.map((log) => {
          const sev = log.severity === "critical" ? "risk-high" : log.severity === "warning" ? "risk-moderate" : "chart-4";
          return (
            <div key={log.id} className="flex items-start gap-3 p-4 hover:bg-accent/30">
              <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full bg-${sev}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium">{log.action}</span>
                  <Badge variant="outline" className="text-[9px] py-0 capitalize">{log.category}</Badge>
                  {log.target && <span className="text-xs text-muted-foreground">→ {log.target}</span>}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  <span className="font-medium">{log.actor}</span>
                  <span className="capitalize"> ({log.actorRole})</span>
                  {log.ip && <span> · {log.ip}</span>}
                  {" · "}
                  {fmtDateTime(log.timestamp)}
                </p>
              </div>
              {log.severity !== "info" && (
                <AlertTriangle className={`h-3.5 w-3.5 shrink-0 ${log.severity === "critical" ? "text-risk-high" : "text-risk-moderate"}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
