/**
 * Shared SHAP feature label humanizer (mirrors backend
 * app/explainability/shap_labels.py).
 *
 * Maps raw, encoded ML feature names into a readable label and a short
 * plain-English description an investigator can understand.
 */

export interface ShapInfo {
  label: string;
  description: string;
}

const SHAP_LABELS: Record<string, ShapInfo> = {
  // ---- Demographics ----
  "Age": { label: "Driver's age", description: "Older/younger drivers fall into historical risk bands." },
  "AgeGroup": { label: "Driver's age group", description: "Age bracket of the policyholder." },
  "AgeOfPolicyHolder": { label: "Policyholder's age", description: "Age of the person who holds the policy." },
  "DriverRating": { label: "Driver risk rating", description: "Internal rating assigned based on past driving record." },
  "Sex": { label: "Driver's gender", description: "Gender of the driver." },
  "MaritalStatus": { label: "Marital status", description: "Marital status of the policyholder." },

  // ---- Policy / coverage ----
  "BasePolicy": { label: "Policy coverage type", description: "Type of base coverage on the policy." },
  "BasePolicy_Collision": { label: "Collision coverage", description: "Policy only covers collision damage." },
  "BasePolicy_Liability": { label: "Liability-only coverage", description: "Policy has minimal, liability-only coverage." },
  "BasePolicy_All Perils": { label: "All-perils coverage", description: "Comprehensive all-perils policy." },
  "PolicyType": { label: "Policy type", description: "Vehicle category combined with coverage type." },
  "Deductible": { label: "Deductible amount", description: "Out-of-pocket amount the customer must pay (higher often correlates with fraud patterns)." },

  // ---- Fault ----
  "Fault": { label: "Who was at fault", description: "Whether the policyholder or a third party was at fault." },
  "Fault_Policy Holder": { label: "Policyholder at fault", description: "The policyholder was at fault in the accident — a known fraud signal." },
  "Fault_Third Party": { label: "Third party at fault", description: "A third party was at fault in the accident." },

  // ---- Timing ----
  "Days:Policy-Accident": { label: "Policy age at time of accident", description: "How soon after buying the policy the accident happened (very recent = suspicious)." },
  "Days:Policy-Claim": { label: "Time from policy to claim", description: "How soon after buying the policy the claim was filed." },
  "Days_Policy_Accident": { label: "Policy age at accident", description: "Days between buying the policy and the accident." },
  "Days_Policy_Claim": { label: "Time from policy to claim", description: "Days between buying the policy and filing the claim." },
  "WeekOfMonth": { label: "Week of the month", description: "Which week of the month the accident occurred." },
  "WeekOfMonthClaimed": { label: "Week claim was filed", description: "Which week of the month the claim was filed." },
  "DayOfWeek": { label: "Day of accident", description: "Day of the week the accident happened." },
  "DayOfWeekClaimed": { label: "Day claim was filed", description: "Day of the week the claim was filed." },
  "Month": { label: "Month of accident", description: "Month the accident occurred." },
  "MonthClaimed": { label: "Month claim was filed", description: "Month the claim was filed." },
  "Year": { label: "Year of accident", description: "Year the accident occurred." },

  // ---- Vehicle ----
  "Make": { label: "Vehicle brand", description: "Manufacturer of the vehicle." },
  "VehicleCategory": { label: "Vehicle category", description: "Type of vehicle (sedan, utility, sport)." },
  "VehicleCategory_Sedan": { label: "Sedan", description: "Vehicle is a sedan." },
  "VehicleCategory_Sport": { label: "Sports car", description: "Vehicle is a sports car." },
  "VehicleCategory_Utility": { label: "Utility/SUV", description: "Vehicle is a utility/SUV." },
  "VehiclePrice": { label: "Vehicle value band", description: "Market-value bracket of the vehicle." },
  "AgeOfVehicle": { label: "Vehicle age", description: "How old the vehicle was at the time of the claim." },

  // ---- Claims history ----
  "PastNumberOfClaims": { label: "Previous claims", description: "Number of prior claims by this customer." },
  "PastNumberOfClaims_none": { label: "No previous claims", description: "Customer has no prior claims." },
  "PastNumberOfClaims_1": { label: "One previous claim", description: "Customer had one prior claim." },
  "PastNumberOfClaims_2 to 4": { label: "2–4 previous claims", description: "Customer has a history of multiple claims." },
  "PastNumberOfClaims_more than 4": { label: "Many previous claims", description: "Customer has more than 4 prior claims — a repeat-filer pattern." },
  "NumberOfSuppliments": { label: "Policy supplements/riders", description: "Number of add-ons or riders attached to the policy." },
  "NumberOfCars": { label: "Vehicles involved", description: "How many vehicles were involved in the incident." },
  "NumberOfCars_1 vehicle": { label: "Single-vehicle incident", description: "Only one vehicle was involved." },
  "NumberOfCars_2 vehicles": { label: "Two-vehicle incident", description: "Two vehicles were involved." },
  "NumberOfCars_3 to 4": { label: "Multi-vehicle incident", description: "3–4 vehicles were involved." },
  "NumberOfCars_5 to 8": { label: "Large multi-vehicle incident", description: "5–8 vehicles were involved." },
  "NumberOfCars_more than 8": { label: "Mass-casualty incident", description: "More than 8 vehicles were involved." },

  // ---- Location / area ----
  "AccidentArea": { label: "Accident area type", description: "Whether the accident happened in an urban or rural area." },
  "AccidentArea_Urban": { label: "Urban accident", description: "Accident happened in an urban area." },
  "AccidentArea_Rural": { label: "Rural accident", description: "Accident happened in a rural area." },

  // ---- Verification signals ----
  "PoliceReportFiled": { label: "Police report", description: "Whether a police report was filed." },
  "PoliceReportFiled_Yes": { label: "Police report filed", description: "A police report was filed for this incident." },
  "PoliceReportFiled_No": { label: "No police report", description: "No police report was filed — common in fraudulent claims." },
  "WitnessPresent": { label: "Witnesses", description: "Whether witnesses were present." },
  "WitnessPresent_Yes": { label: "Witnesses present", description: "Witnesses were present at the scene." },
  "WitnessPresent_No": { label: "No witnesses", description: "No witnesses — harder to verify the claim." },
  "AgentType": { label: "Agent channel", description: "Whether the claim came through an internal or external agent." },
  "AgentType_External": { label: "External agent/broker", description: "Claim handled by an external broker." },
  "AgentType_Internal": { label: "Internal agent", description: "Claim handled by an internal agent." },

  // ---- Address change ----
  "AddressChange-Claim": { label: "Recent address change", description: "Whether the customer changed address around claim time." },
  "AddressChange_Claim": { label: "Recent address change", description: "Whether the customer changed address around claim time." },
  "AddressChange-Claim_under 6 months": { label: "Address changed recently", description: "Address changed within 6 months of the claim — a strong fraud signal." },
  "AddressChange-Claim_1 year": { label: "Address changed ~1 year ago", description: "Address changed about a year ago." },
  "AddressChange-Claim_2 to 3 years": { label: "Address changed 2–3 years ago", description: "Address changed 2–3 years before the claim." },
  "AddressChange-Claim_4 to 8 years": { label: "Old address change", description: "Address changed 4–8 years ago." },
  "AddressChange-Claim_no change": { label: "No address change", description: "No recent address change on file." },

  // ---- Engineered features ----
  "claim_to_premium_ratio": { label: "Claim-to-premium ratio", description: "How large the claim is compared to the annual premium (very high = unusual)." },
  "speed_risk_ratio": { label: "Speed vs. safe limit", description: "Reported speed compared to safe driving speed." },
  "delay_bin": { label: "Reporting delay", description: "How long after the accident the claim was filed." },
  "high_value_claim": { label: "High-value claim", description: "The claim amount is unusually high." },
  "new_policy_claim": { label: "Claim on a new policy", description: "Claim filed shortly after buying the policy — classic fraud pattern." },
  "young_driver_expensive_car": { label: "Young driver, expensive car", description: "Young driver with a high-value vehicle." },
  "multiple_claims_risk": { label: "Multiple claims pattern", description: "Customer has filed multiple claims recently." },
  "late_report_high_value": { label: "Late, high-value claim", description: "High-value claim filed long after the incident." },
  "no_police_high_value": { label: "High value, no police report", description: "Expensive claim with no police report filed." },
  "suspicious_age_claim_combo": { label: "Unusual age + claim pattern", description: "Age and claim type combination rarely seen in legitimate data." },
  "RepNumber": { label: "Representative ID", description: "Internal representative who handled the claim." },

  // ---- Bucketed values that may appear after encoding ----
  "Days:Policy-Accident_1 to 7": { label: "Accident within 1 week of policy", description: "Accident happened within the first week of the policy — strongest fraud signal in the data." },
  "Days:Policy-Accident_8 to 15": { label: "Accident within 2 weeks of policy", description: "Accident happened within 2 weeks of buying the policy." },
  "Days:Policy-Accident_15 to 30": { label: "Accident within a month of policy", description: "Accident happened within the first month of the policy." },
  "Days:Policy-Accident_more than 30": { label: "Accident after 30+ days of policy", description: "Accident happened more than a month into the policy." },
  "Days:Policy-Claim_8 to 15": { label: "Claim filed within 2 weeks", description: "Claim was filed within 2 weeks of buying the policy." },
  "Days:Policy-Claim_15 to 30": { label: "Claim filed within a month", description: "Claim was filed within a month of buying the policy." },
  "Days:Policy-Claim_more than 30": { label: "Claim filed after 30+ days", description: "Claim was filed more than a month into the policy." },
};

/** Backwards-compatible simple label (used by older code). */
export function humanizeFeatureLabel(feature: string): string {
  return humanizeFeature(feature).label;
}

export function humanizeFeature(feature: string): ShapInfo {
  if (SHAP_LABELS[feature]) return SHAP_LABELS[feature];
  const normalized = feature.replace(/[:]/g, "_").replace(/\s+/g, "_");
  if (SHAP_LABELS[normalized]) return SHAP_LABELS[normalized];

  const cleaned = feature.replace(/[_:]/g, " ");
  const label = cleaned.split(/\s+/)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
  return { label: label || feature, description: "This factor influenced the model's fraud assessment." };
}
