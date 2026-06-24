"""
Shared SHAP feature label humanizer.

Maps the raw, encoded feature names that come out of the ML pipeline
(e.g. "Days:Policy-Accident_1 to 7", "Fault_Policy Holder",
"AddressChange-Claim_under 6 months") into plain-English labels and
short descriptions that an investigator can actually understand.

Used by:
- app.explainability.ai_explainer (to craft the narrative)
- the frontend claims/[id] page (mirrored as a TS dictionary)

Keep this in sync with the frontend SHAP_LABELS dictionary in
src/app/app/claims/[id]/page.tsx.
"""
from typing import Tuple


# feature_name -> (human_label, what_it_means)
SHAP_LABELS = {
    # ---- Demographics ----
    "Age": ("Driver's age", "Older/younger drivers fall into historical risk bands."),
    "AgeGroup": ("Driver's age group", "Age bracket of the policyholder."),
    "AgeOfPolicyHolder": ("Policyholder's age", "Age of the person who holds the policy."),
    "DriverRating": ("Driver risk rating", "Internal rating assigned based on past driving record."),
    "Sex": ("Driver's gender", "Gender of the driver."),
    "MaritalStatus": ("Marital status", "Marital status of the policyholder."),

    # ---- Policy / coverage ----
    "BasePolicy": ("Policy coverage type", "Type of base coverage on the policy."),
    "BasePolicy_Collision": ("Collision coverage", "Policy only covers collision damage."),
    "BasePolicy_Liability": ("Liability-only coverage", "Policy has minimal, liability-only coverage."),
    "BasePolicy_All Perils": ("All-perils coverage", "Comprehensive all-perils policy."),
    "PolicyType": ("Policy type", "Vehicle category combined with coverage type."),
    "Deductible": ("Deductible amount", "Out-of-pocket amount the customer must pay (higher often correlates with fraud patterns)."),

    # ---- Fault ----
    "Fault": ("Who was at fault", "Whether the policyholder or a third party was at fault."),
    "Fault_Policy Holder": ("Policyholder at fault", "The policyholder was at fault in the accident — a known fraud signal."),
    "Fault_Third Party": ("Third party at fault", "A third party was at fault in the accident."),

    # ---- Timing ----
    "Days:Policy-Accident": ("Policy age at time of accident", "How soon after buying the policy the accident happened (very recent = suspicious)."),
    "Days:Policy-Claim": ("Time from policy to claim", "How soon after buying the policy the claim was filed."),
    "Days_Policy_Accident": ("Policy age at accident", "Days between buying the policy and the accident."),
    "Days_Policy_Claim": ("Time from policy to claim", "Days between buying the policy and filing the claim."),
    "WeekOfMonth": ("Week of the month", "Which week of the month the accident occurred."),
    "WeekOfMonthClaimed": ("Week claim was filed", "Which week of the month the claim was filed."),
    "DayOfWeek": ("Day of accident", "Day of the week the accident happened."),
    "DayOfWeekClaimed": ("Day claim was filed", "Day of the week the claim was filed."),
    "Month": ("Month of accident", "Month the accident occurred."),
    "MonthClaimed": ("Month claim was filed", "Month the claim was filed."),
    "Year": ("Year of accident", "Year the accident occurred."),

    # ---- Vehicle ----
    "Make": ("Vehicle brand", "Manufacturer of the vehicle."),
    "VehicleCategory": ("Vehicle category", "Type of vehicle (sedan, utility, sport)."),
    "VehicleCategory_Sedan": ("Sedan", "Vehicle is a sedan."),
    "VehicleCategory_Sport": ("Sports car", "Vehicle is a sports car."),
    "VehicleCategory_Utility": ("Utility/SUV", "Vehicle is a utility/SUV."),
    "VehiclePrice": ("Vehicle value band", "Market-value bracket of the vehicle."),
    "AgeOfVehicle": ("Vehicle age", "How old the vehicle was at the time of the claim."),

    # ---- Claims history ----
    "PastNumberOfClaims": ("Previous claims", "Number of prior claims by this customer."),
    "PastNumberOfClaims_none": ("No previous claims", "Customer has no prior claims."),
    "PastNumberOfClaims_1": ("One previous claim", "Customer had one prior claim."),
    "PastNumberOfClaims_2 to 4": ("2–4 previous claims", "Customer has a history of multiple claims."),
    "PastNumberOfClaims_more than 4": ("Many previous claims", "Customer has more than 4 prior claims — a repeat-filer pattern."),
    "NumberOfSuppliments": ("Policy supplements/riders", "Number of add-ons or riders attached to the policy."),
    "NumberOfCars": ("Vehicles involved", "How many vehicles were involved in the incident."),
    "NumberOfCars_1 vehicle": ("Single-vehicle incident", "Only one vehicle was involved."),
    "NumberOfCars_2 vehicles": ("Two-vehicle incident", "Two vehicles were involved."),
    "NumberOfCars_3 to 4": ("Multi-vehicle incident", "3–4 vehicles were involved."),
    "NumberOfCars_5 to 8": ("Large multi-vehicle incident", "5–8 vehicles were involved."),
    "NumberOfCars_more than 8": ("Mass-casualty incident", "More than 8 vehicles were involved."),

    # ---- Location / area ----
    "AccidentArea": ("Accident area type", "Whether the accident happened in an urban or rural area."),
    "AccidentArea_Urban": ("Urban accident", "Accident happened in an urban area."),
    "AccidentArea_Rural": ("Rural accident", "Accident happened in a rural area."),

    # ---- Verification signals ----
    "PoliceReportFiled": ("Police report", "Whether a police report was filed."),
    "PoliceReportFiled_Yes": ("Police report filed", "A police report was filed for this incident."),
    "PoliceReportFiled_No": ("No police report", "No police report was filed — common in fraudulent claims."),
    "WitnessPresent": ("Witnesses", "Whether witnesses were present."),
    "WitnessPresent_Yes": ("Witnesses present", "Witnesses were present at the scene."),
    "WitnessPresent_No": ("No witnesses", "No witnesses — harder to verify the claim."),
    "AgentType": ("Agent channel", "Whether the claim came through an internal or external agent."),
    "AgentType_External": ("External agent/broker", "Claim handled by an external broker."),
    "AgentType_Internal": ("Internal agent", "Claim handled by an internal agent."),

    # ---- Address change ----
    "AddressChange-Claim": ("Recent address change", "Whether the customer changed address around claim time."),
    "AddressChange_Claim": ("Recent address change", "Whether the customer changed address around claim time."),
    "AddressChange-Claim_under 6 months": ("Address changed recently", "Address changed within 6 months of the claim — a strong fraud signal."),
    "AddressChange-Claim_1 year": ("Address changed ~1 year ago", "Address changed about a year ago."),
    "AddressChange-Claim_2 to 3 years": ("Address changed 2–3 years ago", "Address changed 2–3 years before the claim."),
    "AddressChange-Claim_4 to 8 years": ("Old address change", "Address changed 4–8 years ago."),
    "AddressChange-Claim_no change": ("No address change", "No recent address change on file."),

    # ---- Engineered features ----
    "claim_to_premium_ratio": ("Claim-to-premium ratio", "How large the claim is compared to the annual premium (very high = unusual)."),
    "speed_risk_ratio": ("Speed vs. safe limit", "Reported speed compared to safe driving speed."),
    "delay_bin": ("Reporting delay", "How long after the accident the claim was filed."),
    "high_value_claim": ("High-value claim", "The claim amount is unusually high."),
    "new_policy_claim": ("Claim on a new policy", "Claim filed shortly after buying the policy — classic fraud pattern."),
    "young_driver_expensive_car": ("Young driver, expensive car", "Young driver with a high-value vehicle."),
    "multiple_claims_risk": ("Multiple claims pattern", "Customer has filed multiple claims recently."),
    "late_report_high_value": ("Late, high-value claim", "High-value claim filed long after the incident."),
    "no_police_high_value": ("High value, no police report", "Expensive claim with no police report filed."),
    "suspicious_age_claim_combo": ("Unusual age + claim pattern", "Age and claim type combination rarely seen in legitimate data."),
    "RepNumber": ("Representative ID", "Internal representative who handled the claim."),

    # ---- Bucketed values that may appear after encoding ----
    "Days:Policy-Accident_1 to 7": ("Accident within 1 week of policy", "Accident happened within the first week of the policy — strongest fraud signal in the data."),
    "Days:Policy-Accident_8 to 15": ("Accident within 2 weeks of policy", "Accident happened within 2 weeks of buying the policy."),
    "Days:Policy-Accident_15 to 30": ("Accident within a month of policy", "Accident happened within the first month of the policy."),
    "Days:Policy-Accident_more than 30": ("Accident after 30+ days of policy", "Accident happened more than a month into the policy."),
    "Days:Policy-Claim_8 to 15": ("Claim filed within 2 weeks", "Claim was filed within 2 weeks of buying the policy."),
    "Days:Policy-Claim_15 to 30": ("Claim filed within a month", "Claim was filed within a month of buying the policy."),
    "Days:Policy-Claim_more than 30": ("Claim filed after 30+ days", "Claim was filed more than a month into the policy."),
}


def humanize_feature(feature: str) -> Tuple[str, str]:
    """Return (label, description) for a raw SHAP feature name.

    Falls back to a cleaned-up version of the raw name if no mapping exists.
    """
    if feature in SHAP_LABELS:
        return SHAP_LABELS[feature]

    # Try a normalized key (replace ':' and special chars)
    normalized = feature.replace(":", "_").replace(" ", "_")
    if normalized in SHAP_LABELS:
        return SHAP_LABELS[normalized]

    # Fallback: title-case the words
    cleaned = feature.replace("_", " ").replace(":", " ")
    label = " ".join(w.capitalize() for w in cleaned.split())
    return (label or feature, "This factor influenced the model's fraud assessment.")
