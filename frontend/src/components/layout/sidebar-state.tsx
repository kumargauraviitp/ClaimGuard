"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ShellState {
  sidebarCollapsed: boolean;
  mobileOpen: boolean;
  toggleSidebar: () => void;
  setMobileOpen: (v: boolean) => void;
}

export const useShell = create<ShellState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      mobileOpen: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setMobileOpen: (v) => set({ mobileOpen: v }),
    }),
    { name: "claimguard-shell" },
  ),
);
