"use client";

import { PageHeader, PageTransition } from "@/components/layout/page";
import { GlassPanel } from "@/components/ui/claimguard";
import { Button } from "@/components/ui/button";
import { Download, FileText, FileSpreadsheet, Calendar, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

const reports = [
  {
    id: "daily-summary",
    title: "Daily Summary Report",
    description: "Overview of all claims processed today, including fast-tracked approvals and flags.",
    icon: Calendar,
    type: "PDF / CSV",
  },
  {
    id: "weekly-performance",
    title: "Weekly Investigator Performance",
    description: "Metrics on claim resolution times, accuracy, and AI agreement rates by investigator.",
    icon: FileText,
    type: "PDF / Excel",
  },
  {
    id: "monthly-fraud",
    title: "Monthly Fraud Trend Analysis",
    description: "Deep dive into detected fraud patterns, geographic hotspots, and high-risk workshops.",
    icon: AlertTriangle,
    type: "PDF",
  },
  {
    id: "raw-data",
    title: "Raw Claims Export",
    description: "Complete dataset of all claims within a selected date range for external analysis.",
    icon: FileSpreadsheet,
    type: "CSV / Excel",
  },
];

export default function ReportsPage() {
  const handleDownload = (id: string, format: string) => {
    toast.success(`Generating ${format.toUpperCase()} report...`, {
      description: "Your download will start shortly.",
    });
    // Simulate generation time
    setTimeout(() => {
      toast.info("Report downloaded successfully");
    }, 2000);
  };

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Workspace"
        title="Reports & Exports"
        description="Generate and download scheduled reports or raw datasets."
      />

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        {reports.map((report) => (
          <GlassPanel key={report.id} className="flex flex-col p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand/10 text-brand">
                <report.icon className="h-6 w-6" />
              </div>
              <div className="flex-1 space-y-1">
                <h3 className="font-semibold">{report.title}</h3>
                <p className="text-sm text-muted-foreground">{report.description}</p>
                <div className="mt-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Formats: {report.type}
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex flex-wrap gap-3">
              <Button onClick={() => handleDownload(report.id, "pdf")} variant="outline" size="sm" className="gap-2">
                <Download className="h-4 w-4" /> Export PDF
              </Button>
              {report.type.includes("CSV") && (
                <Button onClick={() => handleDownload(report.id, "csv")} variant="outline" size="sm" className="gap-2">
                  <Download className="h-4 w-4" /> Export CSV
                </Button>
              )}
              {report.type.includes("Excel") && (
                <Button onClick={() => handleDownload(report.id, "xlsx")} variant="outline" size="sm" className="gap-2">
                  <Download className="h-4 w-4" /> Export Excel
                </Button>
              )}
            </div>
          </GlassPanel>
        ))}
      </div>
    </PageTransition>
  );
}
