"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeMode = "light" | "dark" | "system";
export type RiskThresholdConfig = {
  low: number; // below = low
  moderate: number; // below = moderate
  elevated: number; // below = elevated, else high
};

export interface AppSettings {
  mockDataEnabled: boolean;
  mockDataNoticeDismissed: boolean;
  riskThresholds: RiskThresholdConfig;
  autoGenerateReports: boolean;
  siuAutoReferral: boolean;
  reduceMotion: boolean;
  compactTables: boolean;
  // feature flag mirror (kept here so the toggle persists)
  flags: Record<string, boolean>;
}

interface SettingsStore extends AppSettings {
  setMockData: (v: boolean) => void;
  dismissMockNotice: () => void;
  setRiskThreshold: (k: keyof RiskThresholdConfig, v: number) => void;
  toggleFlag: (key: string, v?: boolean) => void;
  setSetting: <K extends keyof AppSettings>(k: K, v: AppSettings[K]) => void;
  reset: () => void;
}

const defaults: AppSettings = {
  mockDataEnabled: false,
  mockDataNoticeDismissed: false,
  riskThresholds: { low: 20, moderate: 45, elevated: 70 },
  autoGenerateReports: true,
  siuAutoReferral: true,
  reduceMotion: false,
  compactTables: false,
  flags: {},
};

export const useSettings = create<SettingsStore>()(
  persist(
    (set) => ({
      ...defaults,
      setMockData: (v) => set({ mockDataEnabled: v }),
      dismissMockNotice: () => set({ mockDataNoticeDismissed: true }),
      setRiskThreshold: (k, v) =>
        set((s) => ({ riskThresholds: { ...s.riskThresholds, [k]: v } })),
      toggleFlag: (key, v) =>
        set((s) => ({ flags: { ...s.flags, [key]: v ?? !s.flags[key] } })),
      setSetting: (k, v) => set({ [k]: v } as Partial<SettingsStore>),
      reset: () => set({ ...defaults }),
    }),
    { name: "claimguard-settings" },
  ),
);
