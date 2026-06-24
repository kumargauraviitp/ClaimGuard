import type { Metadata } from "next";
import { AppShell } from "@/components/layout/app-shell";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  title: { default: "Workspace", template: "%s · ClaimGuard" },
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <TooltipProvider delayDuration={0}>
        <AppShell>{children}</AppShell>
      </TooltipProvider>
    </ProtectedRoute>
  );
}
