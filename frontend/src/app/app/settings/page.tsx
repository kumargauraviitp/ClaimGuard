"use client";

import { useSettings } from "@/lib/store";
import { PageTransition, PageHeader, GlassPanel } from "@/components/ui/claimguard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Settings as SettingsIcon, Bell, Palette, Sliders, Zap } from "lucide-react";
import { ModeToggle } from "@/components/layout/mode-toggle";

export default function SettingsPage() {
  const settings = useSettings();

  return (
    <PageTransition>
      <PageHeader eyebrow="System" title="Settings" description="Personalize your ClaimGuard workspace" />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Preferences */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Sliders className="h-4 w-4 text-brand" /><CardTitle className="text-base">Preferences</CardTitle></div>
            <CardDescription>Adjust how the workspace behaves</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Row label="Reduce motion" desc="Minimize animations across the app">
              <Switch checked={settings.reduceMotion} onCheckedChange={(v) => settings.setSetting("reduceMotion", v)} />
            </Row>
            <Separator />
            <Row label="Compact tables" desc="Denser rows for more data on screen">
              <Switch checked={settings.compactTables} onCheckedChange={(v) => settings.setSetting("compactTables", v)} />
            </Row>
            <Separator />
            <Row label="Auto-generate reports" desc="Create investigation reports automatically">
              <Switch checked={settings.autoGenerateReports} onCheckedChange={(v) => settings.setSetting("autoGenerateReports", v)} />
            </Row>
            <Separator />
            <Row label="SIU auto-referral" desc="Refer high-value claims to Special Investigations">
              <Switch checked={settings.siuAutoReferral} onCheckedChange={(v) => settings.setSetting("siuAutoReferral", v)} />
            </Row>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Palette className="h-4 w-4 text-brand" /><CardTitle className="text-base">Appearance</CardTitle></div>
            <CardDescription>Theme & display options</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Row label="Theme mode" desc="Switch between light and dark">
              <ModeToggle />
            </Row>
            <Separator />
            <div className="space-y-2">
              <Label>Language</Label>
              <Select defaultValue="en"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="en">English</SelectItem><SelectItem value="hi">हिन्दी</SelectItem></SelectContent></Select>
            </div>
            <div className="space-y-2">
              <Label>Currency</Label>
              <Select defaultValue="inr"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="inr">₹ INR</SelectItem><SelectItem value="usd">$ USD</SelectItem></SelectContent></Select>
            </div>
          </CardContent>
        </Card>

        {/* Risk thresholds */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Zap className="h-4 w-4 text-brand" /><CardTitle className="text-base">Risk thresholds</CardTitle></div>
            <CardDescription>Customize fraud risk tier boundaries</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {([
              { key: "low" as const, label: "Low", color: "text-risk-low", above: "Below = Low" },
              { key: "moderate" as const, label: "Moderate", color: "text-risk-moderate", above: "Below = Moderate" },
              { key: "elevated" as const, label: "Elevated", color: "text-risk-elevated", above: "Below = Elevated, else High" },
            ]).map((t) => (
              <div key={t.key}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-sm font-medium ${t.color}`}>{t.label} threshold</span>
                  <span className="nums text-sm text-muted-foreground">{settings.riskThresholds[t.key]}%</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={settings.riskThresholds[t.key]}
                  onChange={(e) => settings.setRiskThreshold(t.key, Number(e.target.value))}
                  className="w-full accent-brand"
                />
                <p className="text-[10px] text-muted-foreground mt-1">{t.above}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Bell className="h-4 w-4 text-brand" /><CardTitle className="text-base">Notifications</CardTitle></div>
            <CardDescription>Choose what you get alerted about</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Row label="High-risk flags" desc="Alert when a claim scores above 70%"><Switch defaultChecked /></Row>
            <Separator />
            <Row label="Model drift" desc="Notify on drift threshold breach"><Switch defaultChecked /></Row>
            <Separator />
            <Row label="New claim assignments" desc="When claims are assigned to you"><Switch defaultChecked /></Row>
            <Separator />
            <Row label="Report ready" desc="When investigation reports complete"><Switch /></Row>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <Button variant="outline" onClick={() => { settings.reset(); toast.success("Settings reset to defaults"); }}>Reset to defaults</Button>
        <Button onClick={() => toast.success("Settings saved")} className="bg-brand text-primary-foreground hover:bg-brand/90">Save changes</Button>
      </div>
    </PageTransition>
  );
}

function Row({ label, desc, children }: { label: string; desc: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div><p className="text-sm font-medium">{label}</p><p className="text-xs text-muted-foreground">{desc}</p></div>
      {children}
    </div>
  );
}
