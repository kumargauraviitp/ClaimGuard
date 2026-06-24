// ============================================================
// ClaimGuard domain types
// Centralized type model for the fraud investigation platform.
// ============================================================

export type RiskTier = "low" | "moderate" | "elevated" | "high" | "critical";

export type ClaimStatus =
  | "submitted"
  | "under_review"
  | "investigating"
  | "approved"
  | "rejected"
  | "flagged"
  | "pending_documents";

export type PolicyType =
  | "comprehensive"
  | "third_party"
  | "own_damage"
  | "zero_depreciation"
  | "engine_protect";

export type VehicleType = "sedan" | "suv" | "hatchback" | "luxury" | "commercial" | "two_wheeler";

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  age: number;
  city: string;
  state: string;
  memberSince: string; // ISO date
  previousClaims: number;
  riskScore: number; // 0-100 historical customer risk
}

export interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  type: VehicleType;
  registrationNumber: string;
  color: string;
  marketValue: number;
  odometer: number;
}

export interface Policy {
  id: string;
  policyNumber: string;
  type: PolicyType;
  startDate: string;
  endDate: string;
  premium: number;
  insuredValue: number;
  deductible: number;
  status: "active" | "lapsed" | "expired";
}

export interface ShapFactor {
  feature: string;
  label: string; // human-readable
  description: string; // plain-English explanation of what this factor means
  contribution: number; // percentage points (+/-), e.g. +32
  direction: "increase" | "decrease";
  value: string; // e.g. "₹4,80,000"
  category?: "amount" | "behavior" | "documentation" | "history" | "vehicle" | "policy";
}

export interface AgentOutput {
  id: string;
  claimId: string;
  generatedAt: string;
  orchestratorSummary: string;
  riskAnalysis: string;
  recommendedActions: string[];
  missingDocuments: string[];
  suggestedVerificationSteps: string[];
  ruleViolations: { rule: string; severity: "info" | "warning" | "critical"; detail: string }[];
  finalRecommendation: "approve" | "reject" | "investigate" | "request_documents";
  confidenceLevel: number; // 0-100
  agentTrace: {
    agent: string;
    role: string;
    status: "complete" | "running" | "queued";
    durationMs: number;
    finding: string;
  }[];
}

export interface Claim {
  id: string;
  claimNumber: string; // e.g. CLM-2026-4821
  customerId: string;
  customer: Customer;
  vehicle: Vehicle;
  policy: Policy;
  type: "own_damage" | "third_party" | "theft" | "natural_disaster" | "personal_injury";
  status: ClaimStatus;
  description: string;
  incidentDate: string; // ISO
  reportedDate: string; // ISO
  claimAmount: number;
  approvedAmount?: number;
  incidentLocation: string;
  region: string;
  hasPoliceReport: boolean;
  hasWitnesses: boolean;
  witnessCount: number;
  hasMedicalBills: boolean;
  hasRepairBills: boolean;
  documentsCount: number;
  assignedTo?: string; // investigator name
  createdAt: string;
  // ML / XAI outputs (present when analyzed)
  prediction?: {
    fraudProbability: number; // 0-100
    riskTier: RiskTier;
    confidence: number; // 0-100
    modelVersion: string;
    analyzedAt: string;
  };
  shap?: ShapFactor[];
  agent?: AgentOutput;
  feedback?: {
    id: string;
    final_decision: string;
    investigation_notes?: string;
    timestamp: string;
  }[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  actorRole: "admin" | "investigator" | "manager" | "system";
  action: string;
  category: "claim" | "auth" | "system" | "model" | "admin" | "report";
  target?: string;
  severity: "info" | "warning" | "critical";
  ip?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "investigator" | "manager";
  status: "active" | "invited" | "suspended";
  avatar?: string;
  lastActive: string;
  casesAssigned: number;
  casesResolved: number;
  department: string;
}

export interface FeatureFlag {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
  category: "intelligence" | "workflow" | "integrations" | "experimental";
}

export interface AnalyticsPoint {
  label: string;
  fraudRate: number;
  claimVolume: number;
}

export interface RegionRisk {
  region: string;
  claims: number;
  fraudRate: number;
  riskTier: RiskTier;
}

export interface ModelPerformance {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  falsePositiveRate: number;
  auc: number;
  version: string;
  lastTrained: string;
  driftScore: number;
}
