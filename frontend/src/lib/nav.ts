import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  FilePlus2,
  FolderSearch,
  Brain,
  FileText,
  BarChart3,
  Settings,
  UserCircle,
  ShieldCheck,
  Users,
  ScrollText,
  Flag,
  Gauge,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  description?: string;
  badge?: string;
  roles?: ("admin" | "investigator" | "manager" | "customer")[];
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    label: "Workspace",
    items: [
      { href: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard, description: "Operations overview", roles: ["admin", "investigator", "manager", "customer"] },
      { href: "/app/claims", label: "Claims", icon: FolderSearch, description: "All submitted claims", roles: ["admin", "investigator", "manager", "customer"] },
      { href: "/app/claims/new", label: "New Claim", icon: FilePlus2, description: "Submit a new claim", roles: ["admin", "investigator", "manager", "customer"] },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/app/analysis", label: "Fraud Analysis", icon: Brain, description: "ML + SHAP breakdown", roles: ["admin", "investigator", "manager", "customer"] },
      { href: "/app/investigation", label: "Investigation Report", icon: FileText, description: "AI-generated reports", roles: ["admin", "investigator", "manager", "customer"] },
      { href: "/app/analytics", label: "Analytics", icon: BarChart3, description: "Trends & model perf", roles: ["admin", "investigator", "manager", "customer"] },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/app/admin", label: "Admin Panel", icon: ShieldCheck, description: "System & controls", roles: ["admin", "manager"] },
      { href: "/app/settings", label: "Settings", icon: Settings, roles: ["admin", "investigator", "manager", "customer"] },
      { href: "/app/profile", label: "Profile", icon: UserCircle, roles: ["admin", "investigator", "manager", "customer"] },
    ],
  },
  {
    label: "System Tools",
    items: [
      { href: "/app/intelligence", label: "Intelligence & Drift", icon: Brain, roles: ["admin", "manager", "investigator"] },
      { href: "/app/admin/health", label: "System Health", icon: Gauge, roles: ["admin"] },
      { href: "/app/admin/backup", label: "Backup & Restore", icon: ShieldCheck, roles: ["admin"] },
    ],
  },
];

export const flatNav: NavItem[] = navGroups.flatMap((g) => g.items);

// Used by the command palette / quick search
export const quickNav: NavItem[] = [
  ...flatNav,
  { href: "/app/admin/users", label: "Manage Users", icon: Users, description: "Team & roles" },
  { href: "/app/admin/flags", label: "Feature Flags", icon: Flag, description: "Toggle capabilities" },
  { href: "/app/admin/audit", label: "Audit Log", icon: ScrollText, description: "System activity" },
  { href: "/app/analytics", label: "Model Performance", icon: Gauge, description: "Accuracy & drift" },
];

export const navIconFor = (href: string): LucideIcon =>
  flatNav.find((i) => i.href === href)?.icon ?? LayoutDashboard;
