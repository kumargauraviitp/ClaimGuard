"""
SHAP Feature Humanizer — maps raw ML feature names to plain-English descriptions.

This is Layer 1 of the explanation system: deterministic, no AI needed.
It converts cryptic SHAP keys like "Fault_Policy Holder" into human-readable
sentences like "The policyholder was at fault in the accident (+1.26 → increased risk)".
"""

# Maps raw feature names → human-readable descriptions
# Covers all 116 features the LightGBM model expects
SHAP_LABELS: dict[str, str] = {
    # --- Driver / Customer ---
    "Age": "Driver's age",
    "AgeGroup": "Driver's age group",
    "DriverRating": "Driver's historical risk rating (0 = worst, 5 = best)",
    "Sex": "Driver's gender",

    # --- Policy ---
    "BasePolicy": "Type of insurance policy",
    "BasePolicy_Collision": "Collision coverage policy type",
    "BasePolicy_Liability": "Liability-only policy type (minimal coverage)",
    "BasePolicy_All Perils": "All-perils comprehensive policy type",
    "PolicyType": "Insurance policy type selected",
    "Deductible": "Policy deductible amount (higher = more out-of-pocket before claim pays)",

    # --- Accident ---
    "Fault": "Who was at fault in the accident",
    "Fault_Policy Holder": "The policyholder was at fault in the accident",
    "Fault_Third Party": "A third party was at fault in the accident",
    "AccidentArea": "Where the accident happened",
    "AccidentArea_Rural": "Accident happened in a rural area",
    "AccidentArea_Urban": "Accident happened in an urban area",
    "NumberOfCars": "Number of vehicles involved in the accident",
    "NumberOfCars_2": "Two vehicles involved",
    "NumberOfCars_3": "Three or more vehicles involved",

    # --- Temporal ---
    "WeekOfMonth": "Which week of the month the accident occurred",
    "DayOfWeek": "Day of the week the accident happened",
    "DayOfWeek_Friday": "Accident on a Friday",
    "DayOfWeek_Monday": "Accident on a Monday",
    "DayOfWeek_Saturday": "Accident on a Saturday",
    "DayOfWeek_Sunday": "Accident on a Sunday",
    "DayOfWeek_Thursday": "Accident on a Thursday",
    "DayOfWeek_Tuesday": "Accident on a Tuesday",
    "DayOfWeek_Wednesday": "Accident on a Wednesday",
    "Month": "Month of the year the accident occurred",
    "Month_Apr": "Accident in April",
    "Month_Aug": "Accident in August",
    "Month_Dec": "Accident in December",
    "Month_Feb": "Accident in February",
    "Month_Jan": "Accident in January",
    "Month_Jul": "Accident in July",
    "Month_Jun": "Accident in June",
    "Month_Mar": "Accident in March",
    "Month_May": "Accident in May",
    "Month_Nov": "Accident in November",
    "Month_Oct": "Accident in October",
    "Month_Sep": "Accident in September",
    "Year": "Year of the accident (model was trained on 1994-1996 data)",
    "Days_Policy_Accident": "Days between buying the policy and the accident (shorter = newer policy = more suspicious)",
    "Days_Policy_Claim": "Days between buying the policy and filing the claim",
    "AgeOfPolicyHolder": "Policyholder's age at the time of the accident",

    # --- Vehicle ---
    "VehicleCategory": "Category of the vehicle",
    "VehicleCategory_Sedan": "Sedan-type vehicle",
    "VehicleCategory_Sport": "Sports car",
    "VehicleCategory_Utility": "Utility vehicle (SUV, truck)",
    "Make": "Vehicle manufacturer brand",
    "vehicle_age_engineered": "How old the vehicle is (older vehicles may have higher claim rates)",

    # --- Address / Location ---
    "AddressChange_Claim": "Policyholder changed address at the time of claim",
    "AddressChange": "How recently the customer changed their address",
    "AddressChange_0 to 6 months": "Address changed within the last 6 months",
    "AddressChange_1 to 2 years": "Address changed 1-2 years ago",
    "AddressChange_2 to 3 years": "Address changed 2-3 years ago",
    "AddressChange_3 to 6 months": "Address changed 3-6 months ago",
    "AddressChange_more than 3 years": "Address has been the same for over 3 years",
    "AddressChange_no change": "No address change on file",

    # --- Past Claims ---
    "PastNumberOfClaims": "Total number of previous insurance claims by this policyholder",
    "PastNumberOfClaims_0": "No previous claims",
    "PastNumberOfClaims_1": "One previous claim",
    "PastNumberOfClaims_2 to 4": "Two to four previous claims (frequent claimer)",
    "PastNumberOfClaims_more than 4": "More than four previous claims (very high frequency)",
    "NumberOfClaims_Past5Years": "How many claims in the past 5 years",

    # --- Financial ---
    "ClaimAmount": "Amount of money being claimed",
    "InsuredAge": "Age of the insured person (years since birth)",
    "WitnessPresent": "Whether witnesses were present at the accident",
    "WitnessPresent_No": "No witnesses present at the accident",
    "WitnessPresent_Yes": "Witnesses were present at the accident",
    "AgentType": "Type of insurance agent or broker",
    "AgentType_External": "Claim handled by an external agent",
    "AgentType_Internal": "Claim handled by an internal agent",

    # --- Engineered / Interaction features ---
    "claim_to_premium_ratio": "How large the claim is compared to the annual premium",
    "speed_risk_ratio": "Vehicle speed relative to typical safe driving speed",
    "delay_bin": "How long after the accident the claim was filed",
    "high_value_claim": "Whether the claim amount is unusually high",
    "new_policy_claim": "Claim filed shortly after buying the policy",
    "young_driver_expensive_car": "Young driver with an expensive vehicle",
    "multiple_claims_risk": "Pattern of multiple claims by the same person",
    "late_report_high_value": "Claim filed late AND for a high amount",
    "no_police_high_value": "No police report for a high-value claim",
    "suspicious_age_claim_combo": "Unusual combination of driver age and claim pattern",
}


def humanize_feature(feature: str) -> str:
    """Convert a raw SHAP feature key to a human-readable label.
    Falls back to a cleaned-up version of the raw key."""
    if feature in SHAP_LABELS:
        return SHAP_LABELS[feature]
    # Fallback: replace underscores, capitalize
    return feature.replace("_", " ").replace("Engineered", "factor").title()


def humanize_shap_explanation(feature: str, value: float) -> str:
    """Generate a full human-readable sentence for one SHAP factor.
    Returns something like:
    'The policyholder was at fault in the accident — this increased fraud risk'
    """
    label = humanize_feature(feature)
    direction = "increased fraud risk" if value > 0 else "decreased fraud risk"
    magnitude = abs(value)
    severity = "strongly" if magnitude > 0.5 else "moderately" if magnitude > 0.2 else "slightly"

    return f"{label} — this {severity} {direction}"
