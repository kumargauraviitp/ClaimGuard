from pydantic import BaseModel, EmailStr, UUID4, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from app.feedback.schemas import FeedbackResponse

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    identity_type: Optional[str] = None
    identity_number: Optional[str] = None
    dl_number: Optional[str] = None
    dl_expiry_date: Optional[datetime] = None

class CustomerResponse(CustomerBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Policy Schemas ---
class PolicyBase(BaseModel):
    policy_number: str
    policy_type: str
    policy_holder_name: Optional[str] = None
    start_date: datetime
    end_date: datetime
    premium: float
    deductible: float
    coverage_limit: float
    no_claim_bonus: Optional[float] = None
    status: str = "active"

class PolicyResponse(PolicyBase):
    id: UUID4
    customer_id: UUID4
    class Config:
        from_attributes = True

# --- Vehicle Schemas ---
class VehicleBase(BaseModel):
    vin: str
    make: str
    model: str
    variant: Optional[str] = None
    year: int
    purchase_year: Optional[int] = None
    license_plate: str
    color: Optional[str] = None
    vehicle_type: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    engine_number: Optional[str] = None
    chassis_number: Optional[str] = None
    purchase_price: Optional[float] = None
    current_market_value: Optional[float] = None

class VehicleResponse(VehicleBase):
    id: UUID4
    class Config:
        from_attributes = True

# --- Accident Schemas ---
class AccidentBase(BaseModel):
    incident_date: date
    incident_time: Optional[str] = None
    accident_location: Optional[str] = None
    gps_coordinates: Optional[str] = None
    road_type: Optional[str] = None
    road_condition: Optional[str] = None
    weather_condition: Optional[str] = None
    accident_description: Optional[str] = None
    vehicle_speed: Optional[int] = None
    number_of_vehicles_involved: Optional[int] = None
    number_of_injured: Optional[int] = None
    fatalities: Optional[int] = None

class AccidentResponse(AccidentBase):
    id: UUID4
    class Config:
        from_attributes = True

# --- Financial Schemas ---
class FinancialDetailsBase(BaseModel):
    claim_amount: float
    repair_estimate: Optional[float] = None
    medical_expenses: Optional[float] = None
    hospital_charges: Optional[float] = None
    towing_charges: Optional[float] = None
    vehicle_recovery_charges: Optional[float] = None
    other_expenses: Optional[float] = None
    total_claim_amount: Optional[float] = None

class FinancialDetailsResponse(FinancialDetailsBase):
    id: UUID4
    class Config:
        from_attributes = True

# --- Police Schemas ---
class PoliceDetailsBase(BaseModel):
    police_report_available: bool = False
    fir_number: Optional[str] = None
    police_station: Optional[str] = None
    police_district: Optional[str] = None
    officer_name: Optional[str] = None
    officer_contact: Optional[str] = None

class PoliceDetailsResponse(PoliceDetailsBase):
    id: UUID4
    class Config:
        from_attributes = True

# --- Witness Schemas ---
class WitnessBase(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    statement: Optional[str] = None
    identity_proof: Optional[str] = None

class WitnessResponse(WitnessBase):
    id: UUID4
    class Config:
        from_attributes = True

# --- Prediction Schemas ---
class RuleFlagResponse(BaseModel):
    rule: str
    label: str
    reason: str
    score_added: float

class PredictionResponse(BaseModel):
    id: UUID4
    fraud_probability: float
    risk_category: str
    prediction_confidence: float
    shap_explanations: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    llm_cross_check_flag: Optional[bool] = None
    llm_cross_check_reasoning: Optional[str] = None
    rule_flags: Optional[List[RuleFlagResponse]] = None
    explanation: Optional[str] = None
    base_ml_probability: Optional[float] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- Claim Schemas ---
class ClaimBase(BaseModel):
    claim_number: str
    reporting_delay_days: Optional[int] = None
    status: str = "draft"
    workflow_status: Optional[str] = None

class ClaimResponse(ClaimBase):
    id: UUID4
    policy_id: UUID4
    customer_id: UUID4
    vehicle_id: Optional[UUID4] = None
    filing_date: datetime
    created_at: datetime
    updated_at: datetime
    
    customer: Optional[CustomerResponse] = None
    vehicle: Optional[VehicleResponse] = None
    accident: Optional[AccidentResponse] = None
    financial_details: Optional[FinancialDetailsResponse] = None
    police_details: Optional[PoliceDetailsResponse] = None
    witnesses: List[WitnessResponse] = []
    predictions: List[PredictionResponse] = []
    feedback: List['FeedbackResponse'] = []

    class Config:
        from_attributes = True

class ClaimSubmissionWizard(BaseModel):
    """Matches the Next.js form state for easier integration"""
    # System
    status: str = "submitted" # draft | submitted

    # Customer Details
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None

    # Vehicle Details
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    regNumber: Optional[str] = None
    color: Optional[str] = None
    vehicle_type: Optional[str] = None
    fuel_type: Optional[str] = None
    purchase_price: Optional[float] = None
    current_market_value: Optional[float] = None

    # Policy Details
    policyType: Optional[str] = None
    policyNumber: Optional[str] = None
    insuredValue: Optional[float] = None

    # Accident Details
    type: Optional[str] = None # claim type
    incidentDate: Optional[str] = None # "YYYY-MM-DD"
    location: Optional[str] = None
    weather_conditions: Optional[str] = None
    road_conditions: Optional[str] = None
    description: Optional[str] = None
    vehicle_speed: Optional[int] = None
    number_of_vehicles_involved: Optional[int] = None
    number_of_injured: Optional[int] = None

    # Claim Details
    claimAmount: Optional[float] = None
    repair_estimate: Optional[float] = None
    medical_expenses: Optional[float] = None
    hospital_charges: Optional[float] = None
    towing_charges: Optional[float] = None
    additional_expenses: Optional[float] = None

    # Police Information
    hasPoliceReport: str = "no" # "yes" / "no"
    police_report_number: Optional[str] = None
    police_station: Optional[str] = None

    # Witness Details
    witnesses: str = "no"       # "yes" / "no"
    witness_name: Optional[str] = None
    witness_contact: Optional[str] = None
    witness_details: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _empty_str_to_none(cls, values):
        """The Next.js form holds every field as a string, so unfilled fields
        arrive as "" (empty string). Pydantic treats "" as an invalid value for
        Optional[int]/Optional[float]/Optional[EmailStr] fields and returns 422.
        Normalize blank strings to None here so submissions never 422 on blanks."""
        if not isinstance(values, dict):
            return values
        # hasPoliceReport/witnesses are required str enums ("yes"/"no") — keep them.
        enum_fields = {"hasPoliceReport", "witnesses"}
        for key, val in values.items():
            if key in enum_fields:
                continue
            if isinstance(val, str) and val.strip() == "":
                values[key] = None
        return values

# --- Preprocessing Schemas ---
class PreprocessingRunRequest(BaseModel):
    claim_id: UUID4

class PreprocessingRunResponse(BaseModel):
    claim_id: UUID4
    status: str
    feature_vector: Optional[List[float]] = None
    processing_time_ms: int
    missing_values_imputed: int
    features_engineered: int
    warnings: List[str] = []
    errors: List[str] = []

class PreprocessingLogResponse(BaseModel):
    id: UUID4
    claim_id: UUID4
    status: str
    processing_time_ms: Optional[int] = None
    missing_values_imputed: int
    features_engineered: int
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    created_at: datetime
    class Config:
        from_attributes = True

class PreprocessingValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []

# --- Dashboard KPIs ---
class DashboardKPIs(BaseModel):
    totalClaims: int
    fraudDetected: int
    fraudRate: float
    openInvestigations: int
    avgConfidence: float
    falsePositiveRate: float
    avgProcessingHours: int
    investigatorProductivity: float
    recoveredValue: float
    totalClaimValue: float

# --- Training & Model Selection Schemas ---
class LeaderboardItem(BaseModel):
    rank: int
    id: str
    label: str
    sampler: str
    model: str
    metrics: Dict[str, float]
    score: float
    training_time: Optional[str] = None
    is_tuned: Optional[bool] = False
    mlflow_run_url: Optional[str] = None
    model_registry_version: Optional[str] = None

class TrainingStatusResponse(BaseModel):
    status: str
    progress: float
    current_step: str
    errors: List[str] = []
    leaderboard: Optional[List[LeaderboardItem]] = None
    tuned_leaderboard: Optional[List[LeaderboardItem]] = None

class ModelSelectionRequest(BaseModel):
    experiment_id: str

class ModelSelectionResponse(BaseModel):
    status: str
    message: str
    experiment_id: str
    model_registry_version: Optional[str] = None
