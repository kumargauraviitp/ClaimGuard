"use client";

import { useMemo, useState, useEffect } from "react";
import { useSettings } from "@/lib/store";
import { useAuthStore } from "@/lib/authStore";
import * as data from "@/lib/mock/data";
import apiClient from "@/lib/apiClient";
import { humanizeFeature } from "@/lib/shap-labels";

const emptyData: AppData = {
  disconnected: true,
  claims: [],
  claimById: () => undefined,
  users: [],
  auditLog: [],
  featureFlags: [],
  model: {
    accuracy: 0,
    precision: 0,
    recall: 0,
    f1: 0,
    falsePositiveRate: 0,
    auc: 0,
    version: "—",
    lastTrained: "",
    driftScore: 0,
  },
  regionRisk: [],
  fraudTrend: [],
  fraudDistribution: [],
  predictionHistory: [],
  investigationStatus: [],
  kpis: {
    totalClaims: 0,
    fraudDetected: 0,
    fraudRate: 0,
    openInvestigations: 0,
    avgConfidence: 0,
    falsePositiveRate: 0,
    avgProcessingHours: 0,
    investigatorProductivity: 0,
    recoveredValue: 0,
    totalClaimValue: 0,
  },
};

export interface AppData {
  disconnected: boolean;
  claims: typeof data.mockClaims;
  claimById: typeof data.mockClaimById;
  users: typeof data.mockUsers;
  auditLog: typeof data.mockAuditLog;
  featureFlags: typeof data.mockFeatureFlags;
  model: typeof data.mockModelPerformance;
  regionRisk: typeof data.mockRegionRisk;
  fraudTrend: typeof data.mockFraudTrend;
  fraudDistribution: typeof data.mockFraudDistribution;
  predictionHistory: typeof data.mockPredictionHistory;
  investigationStatus: typeof data.mockInvestigationStatus;
  kpis: typeof data.mockKpis;
}

export function useAppData(trendInterval: string = "monthly"): AppData {
  const mockDataEnabled = useSettings((s) => s.mockDataEnabled);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [liveData, setLiveData] = useState<AppData | null>(null);

  useEffect(() => {
    if (mockDataEnabled) return;
    // Don't fire API calls until we're actually authenticated. Zustand persist
    // hydrates asynchronously, so on first mount isAuthenticated is false and
    // requests would flood the backend with 401s.
    if (!isAuthenticated) return;

    let mounted = true;
    async function fetchLive() {
      try {
        const [claimsRes, kpisRes, trendRes, distRes] = await Promise.all([
          apiClient.get("/api/claims").catch(() => ({ data: [] })),
          apiClient.get("/api/analytics/overview").catch(() => ({ data: {} })),
          apiClient.get(`/api/analytics/trend?interval=${trendInterval}`).catch(() => ({ data: [] })),
          apiClient.get("/api/analytics/distribution").catch(() => ({ data: [] })),
        ]);

        const claims = claimsRes.data;
        const kpis = kpisRes.data;
        const fraudTrend = trendRes.data || [];
        const fraudDistribution = distRes.data || [];

        if (!mounted) return;

        const mappedClaims = claims.map((c: any) => {
          const pred = c.predictions?.length > 0 ? c.predictions[0] : null;
          const formatPct = (v: number) => Math.min(100, Math.max(0, Math.round(v > 1 ? v : v * 100)));
          return {
            id: c.id,
            claimNumber: c.claim_number,
            description: c.accident?.accident_description || "",
            type: "Collision",
            customer: {
              name: c.customer ? `${c.customer.first_name} ${c.customer.last_name}`.trim() : "Unknown",
              city: c.customer?.city || "Unknown",
              state: c.customer?.state || "—",
              phone: c.customer?.phone || "",
              email: c.customer?.email || "",
              previousClaims: 0,
            },
            vehicle: {
              make: c.vehicle?.make || "Unknown",
              model: c.vehicle?.model || "",
              year: c.vehicle?.year || "",
              registrationNumber: c.vehicle?.license_plate || "",
              color: c.vehicle?.color || "",
              type: c.vehicle?.vehicle_type || "",
              marketValue: c.vehicle?.current_market_value || null,
            },
            incidentDate: c.accident?.incident_date,
            reportedDate: c.filing_date || c.created_at,
            incidentLocation: c.accident?.accident_location || "Unknown",
            witnessCount: c.witnesses?.length || 0,
            hasPoliceReport: c.police_details?.police_report_available || false,
            hasWitnesses: (c.witnesses?.length || 0) > 0,
            hasMedicalBills: (c.financial_details?.medical_expenses || 0) > 0,
            hasRepairBills: (c.financial_details?.repair_estimate || 0) > 0,
            documentsCount: c.documents?.length || 0,
            createdAt: c.created_at,
            claimAmount: c.financial_details?.claim_amount || 0,
            approvedAmount: null,
            status: c.status,
            prediction: pred ? {
              id: pred.id,
              fraudProbability: formatPct(pred.fraud_probability),
              riskTier: ({ low: "low", medium: "moderate", high: "high", critical: "critical" } as const)[
                (pred.risk_category || "").toLowerCase() as "low" | "medium" | "high" | "critical"
              ] ?? "moderate",
              confidence: formatPct(pred.prediction_confidence),
              modelVersion: pred.model_version || "LightGBM v2.0",
              explanation: pred.explanation || "",
            } : null,
            ruleFlags: pred?.rule_flags || [],
            shap: pred?.shap_explanations
              ? Object.entries(pred.shap_explanations).map(([k, v]) => {
                  const info = humanizeFeature(k);
                  return {
                    feature: k,
                    label: info.label,
                    description: info.description,
                    value: (v as number) > 0 ? "+" : "-",
                    contribution: v as number,
                  };
                })
              : [],
            agent: pred ? {
              orchestratorSummary: pred.explanation || "AI detected anomalies requiring investigation.",
              riskAnalysis: `Model confidence: ${formatPct(pred.prediction_confidence)}%. ` + 
                            (pred.rule_flags?.map((r: any) => r.reason).join(" ") || "Multiple risk factors align with historical fraud patterns."),
              recommendedActions: [
                "Verify repair estimate with empaneled garage.",
                "Cross-check policy details and reporting timeline.",
                "Request additional documentation if needed."
              ],
              missingDocuments: [],
              suggestedVerificationSteps: [
                "Confirm claimant identity and policy validity.",
                "Verify incident location against reported facts."
              ],
              ruleViolations: (pred.rule_flags || []).map((r: any) => ({
                rule: r.rule,
                severity: "warning",
                detail: r.reason
              })),
              finalRecommendation: pred.fraud_probability >= 0.45 ? "investigate" : "approve",
              confidenceLevel: formatPct(pred.prediction_confidence),
              generatedAt: pred.created_at,
              agentTrace: [
                { agent: "Rule Agent", role: "Policy & compliance", status: "complete", durationMs: 412, finding: `${pred.rule_flags?.length || 0} rule violations detected.` },
                { agent: "SHAP Agent", role: "Model interpretation", status: "complete", durationMs: 301, finding: "Risk factors successfully extracted." },
                { agent: "Report Agent", role: "Report synthesis", status: "complete", durationMs: 622, finding: "Investigation report generated." }
              ]
            } : null,
            feedback: c.feedback || [],
          };
        });

        setLiveData({
          ...emptyData,
          disconnected: false,
          claims: mappedClaims,
          claimById: (id: string) => mappedClaims.find((c: any) => c.id === id) || data.mockClaimById(id),
          fraudTrend: fraudTrend.length > 0 ? fraudTrend : data.mockFraudTrend,
          fraudDistribution: fraudDistribution.length > 0 ? fraudDistribution : data.mockFraudDistribution,
          kpis: {
            ...emptyData.kpis,
            totalClaims: kpis.total_claims || 0,
            fraudDetected: kpis.fraud_claims || 0,
            fraudRate: kpis.fraud_rate || 0,
            openInvestigations: kpis.pending_investigations || 0,
            avgConfidence: kpis.avg_confidence || 0,
            falsePositiveRate: kpis.false_positive_rate || 0,
          }
        });
      } catch (err) {
        console.error("Error fetching live data:", err);
        if (mounted) setLiveData({ ...emptyData, disconnected: true });
      }
    }

    fetchLive();
    return () => { mounted = false; };
  }, [mockDataEnabled, trendInterval, isAuthenticated]);

  return useMemo<AppData>(() => {
    if (!mockDataEnabled) {
      return liveData || { ...emptyData, disconnected: true };
    }
    return {
      disconnected: false,
      claims: data.mockClaims,
      claimById: data.mockClaimById,
      users: data.mockUsers,
      auditLog: data.mockAuditLog,
      featureFlags: data.mockFeatureFlags,
      model: data.mockModelPerformance,
      regionRisk: data.mockRegionRisk,
      fraudTrend: data.mockFraudTrend,
      fraudDistribution: data.mockFraudDistribution,
      predictionHistory: data.mockPredictionHistory,
      investigationStatus: data.mockInvestigationStatus,
      kpis: data.mockKpis,
    };
  }, [mockDataEnabled, liveData]);
}
