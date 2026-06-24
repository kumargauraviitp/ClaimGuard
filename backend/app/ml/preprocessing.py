import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session

from app import models

class PreprocessingException(Exception):
    pass

class DataPreprocessor:
    def __init__(self, db: Session):
        self.db = db
        self.artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts")
        self.pipeline_path = os.path.join(self.artifacts_dir, "production.pkl")
        
        self.wrapper_pipeline = None
        
        self.logs = {
            "missing_values_imputed": 0,
            "features_engineered": 0,
            "warnings": [],
            "errors": []
        }

    def _load_artifacts(self):
        if not os.path.exists(self.pipeline_path):
            raise PreprocessingException("production.pkl missing. Ensure model is trained.")
            
        self.wrapper_pipeline = joblib.load(self.pipeline_path)

    def _map_age(self, age: int) -> str:
        if age <= 17: return "16 to 17"
        elif age <= 20: return "18 to 20"
        elif age <= 25: return "21 to 25"
        elif age <= 30: return "26 to 30"
        elif age <= 35: return "31 to 35"
        elif age <= 40: return "36 to 40"
        elif age <= 50: return "41 to 50"
        elif age <= 65: return "51 to 65"
        else: return "over 65"

    def _map_vehicle_price(self, price: float) -> str:
        if not price or price < 20000: return "less than 20,000"
        elif price <= 29000: return "20,000 to 29,000"
        elif price <= 39000: return "30,000 to 39,000"
        elif price <= 59000: return "40,000 to 59,000"
        elif price <= 69000: return "60,000 to 69,000"
        else: return "more than 69,000"

    def _map_vehicle_age(self, year: int) -> str:
        if not year: return "7 years"
        age = datetime.now().year - year
        if age <= 0: return "new"
        elif age <= 2: return "2 years"
        elif age <= 3: return "3 years"
        elif age <= 4: return "4 years"
        elif age <= 5: return "5 years"
        elif age <= 6: return "6 years"
        elif age <= 7: return "7 years"
        else: return "more than 7"

    def _map_past_claims(self, claims_count: int) -> str:
        if not claims_count or claims_count == 0: return "none"
        elif claims_count == 1: return "1"
        elif claims_count <= 4: return "2 to 4"
        else: return "more than 4"

    @staticmethod
    def _map_report_delay(days: int) -> str:
        """Map claim-reporting delay to Fraud Oracle 'Days:Policy-Claim' bucket."""
        if days <= 0: return "8 to 15"   # same-day reporting falls into shortest bucket
        if days <= 7: return "8 to 15"
        if days <= 15: return "8 to 15"
        if days <= 30: return "15 to 30"
        return "more than 30"

    @staticmethod
    def _map_policy_age(days: int) -> str:
        """Map policy age at accident time to Fraud Oracle 'Days:Policy-Accident' bucket.
        Brand-new policies (<=7 days) are the strongest fraud signal in the dataset."""
        if days <= 7: return "1 to 7"
        if days <= 15: return "8 to 15"
        if days <= 30: return "15 to 30"
        return "more than 30"

    @staticmethod
    def _clamp_deductible(deductible: float) -> int:
        """Map real-world deductible to the training distribution {300, 400, 500, 700}.
        Training data (carclaims.csv) only has these 4 values. Values outside this
        range produce extreme StandardScaler outputs that destroy model discrimination."""
        if not deductible or deductible <= 0:
            return 400  # default mid-range
        if deductible <= 350:
            return 300
        elif deductible <= 450:
            return 400
        elif deductible <= 600:
            return 500
        else:
            return 700  # high deductible

    @staticmethod
    def _clamp_year(year: int) -> int:
        """Map real-world vehicle year to training distribution {1994, 1995, 1996}.
        Training data only has these 3 years. The actual value doesn't carry fraud signal —
        what matters is AgeOfVehicle (derived separately). We map to 1996 (newest) as
        a neutral default so the StandardScaler doesn't produce extreme outliers."""
        if not year:
            return 1996
        return 1996  # neutral; signal is captured by AgeOfVehicle bucket instead

    @staticmethod
    def _map_accident_fault(claim) -> str:
        """Infer 'Fault' (Policy Holder vs Third Party) from number of vehicles involved.
        Single-vehicle accidents default to 'Policy Holder' fault — a key fraud signal."""
        n_vehicles = None
        if claim.accident and getattr(claim.accident, "number_of_vehicles_involved", None):
            n_vehicles = claim.accident.number_of_vehicles_involved
        return "Third Party" if (n_vehicles and n_vehicles >= 2) else "Policy Holder"

    @staticmethod
    def _map_address_change(claim) -> str:
        """Recent address change near claim time is a fraud red flag.
        Derived from the gap between policy start and claim filing."""
        if not claim.policy or not claim.policy.start_date or not claim.created_at:
            return "no change"
        # Use policy novelty as a proxy: very new policy suggests recently changed circumstances
        try:
            policy_age_days = (claim.created_at.date() - claim.policy.start_date.date()).days
        except Exception:
            return "no change"
        if policy_age_days <= 180: return "under 6 months"   # strong fraud signal
        if policy_age_days <= 365: return "1 year"
        if policy_age_days <= 1095: return "2 to 3 years"
        if policy_age_days <= 2920: return "4 to 8 years"
        return "no change"

    @staticmethod
    def _map_agent_type(claim) -> str:
        """External vs Internal agent. External (broker) channels carry more fraud risk."""
        created_by = (claim.created_by or "").lower() if getattr(claim, "created_by", None) else ""
        return "Internal" if "internal" in created_by or "staff" in created_by else "External"

    def _retrieve_claim_data(self, claim_id: str) -> Dict[str, Any]:
        claim = self.db.query(models.Claim).filter(models.Claim.id == claim_id).first()
        if not claim:
            raise PreprocessingException(f"Claim ID {claim_id} not found in database.")

        if not claim.customer or not claim.vehicle or not claim.policy:
            raise PreprocessingException("Incomplete record: Missing Customer, Vehicle, or Policy.")

        incident_date = claim.accident.incident_date if claim.accident and claim.accident.incident_date else datetime.now()
        report_date = claim.created_at or datetime.now()
        policy_date = claim.policy.start_date if claim.policy and claim.policy.start_date else (incident_date - pd.Timedelta(days=365))

        days_policy_accident = (incident_date.date() - policy_date.date()).days if hasattr(incident_date, "date") else (incident_date - policy_date).days
        days_policy_claim = (report_date.date() - policy_date.date()).days if hasattr(report_date, "date") else (report_date - policy_date).days

        age = claim.customer.age if getattr(claim.customer, "age", None) else 30
        vehicle_price = claim.vehicle.current_market_value if getattr(claim.vehicle, "current_market_value", None) else 25000
        past_claims = len(claim.customer.claims) - 1 if hasattr(claim.customer, "claims") and claim.customer.claims else 0
        if past_claims < 0: past_claims = 0

        # Vehicle category derived from real vehicle metadata (Utility = SUVs/trucks)
        vtype = (getattr(claim.vehicle, "vehicle_type", None) or "").lower()
        model = (getattr(claim.vehicle, "model", "") or "").lower()
        if vtype in ("suv", "truck", "pickup", "minivan") or any(k in model for k in ["x5", "x3", "rav4", "cr-v", "suv", "fortuner", "scorpio"]):
            vehicle_category = "Utility"
        elif vtype in ("sedan", "hatchback", "coupe") or vtype == "":
            vehicle_category = "Sedan"
        else:
            vehicle_category = "Sport"

        # Map UI policy_type strings (e.g. "Comprehensive") to Fraud Oracle BasePolicy categories
        raw_pt = (claim.policy.policy_type or "").lower() if claim.policy and claim.policy.policy_type else ""
        if "all peril" in raw_pt or "comprehensive" in raw_pt or "own damage" in raw_pt:
            base_policy = "All Perils"
        elif "collision" in raw_pt:
            base_policy = "Collision"
        elif "liability" in raw_pt or "third party" in raw_pt:
            base_policy = "Liability"
        else:
            base_policy = "All Perils"
        policy_type = f"{vehicle_category} - {base_policy}"

        # Real fraud-signal features (previously hardcoded — these are top SHAP drivers)
        fault = self._map_accident_fault(claim)
        address_change = self._map_address_change(claim)
        agent_type = self._map_agent_type(claim)
        police_filed = "Yes" if (claim.police_details and claim.police_details.police_report_available) else "No"
        witness_present = "Yes" if (claim.witnesses and len(claim.witnesses) > 0) else "No"

        # NumberOfSuppliments: proxy from documents count (more docs = more supplements/riders)
        n_docs = len(claim.documents) if hasattr(claim, "documents") and claim.documents else 0
        if n_docs == 0:
            suppliments = "none"
        elif n_docs <= 2:
            suppliments = "1 to 2"
        elif n_docs <= 5:
            suppliments = "3 to 5"
        else:
            suppliments = "more than 5"

        # NumberOfCars: infer from vehicles involved in the accident
        n_vehicles = claim.accident.number_of_vehicles_involved if claim.accident and getattr(claim.accident, "number_of_vehicles_involved", None) else 1
        if n_vehicles == 1:
            number_of_cars = "1 vehicle"
        elif n_vehicles == 2:
            number_of_cars = "2 vehicles"
        elif n_vehicles <= 4:
            number_of_cars = "3 to 4"
        elif n_vehicles <= 8:
            number_of_cars = "5 to 8"
        else:
            number_of_cars = "more than 8"

        # MaritalStatus not in schema — default to Single (higher fraud risk per dataset)
        marital_status = "Single"

        data = {
            "Month": incident_date.strftime("%b"),
            "WeekOfMonth": min((incident_date.day - 1) // 7 + 1, 5),
            "DayOfWeek": incident_date.strftime("%A"),
            "Make": claim.vehicle.make if claim.vehicle.make else "Honda",
            "AccidentArea": "Urban",
            "DayOfWeekClaimed": report_date.strftime("%A"),
            "MonthClaimed": report_date.strftime("%b"),
            "WeekOfMonthClaimed": min((report_date.day - 1) // 7 + 1, 5),
            "Sex": claim.customer.gender.capitalize() if claim.customer and claim.customer.gender else "Male",
            "MaritalStatus": marital_status,
            "Age": age,
            "Fault": fault,
            "PolicyType": policy_type,
            "VehicleCategory": vehicle_category,
            "VehiclePrice": self._map_vehicle_price(vehicle_price),
            "PolicyNumber": claim.policy.policy_number if claim.policy else "123",
            "RepNumber": 1,
            "Deductible": self._clamp_deductible(claim.policy.deductible if claim.policy else 400),
            "DriverRating": 1,
            "Days:Policy-Accident": self._map_policy_age(days_policy_accident),
            "Days:Policy-Claim": self._map_report_delay(days_policy_claim),
            "PastNumberOfClaims": self._map_past_claims(past_claims),
            "AgeOfVehicle": self._map_vehicle_age(claim.vehicle.year if claim.vehicle else 2019),
            "AgeOfPolicyHolder": self._map_age(age),
            "PoliceReportFiled": police_filed,
            "WitnessPresent": witness_present,
            "AgentType": agent_type,
            "NumberOfSuppliments": suppliments,
            "AddressChange-Claim": address_change,
            "NumberOfCars": number_of_cars,
            "Year": self._clamp_year(claim.vehicle.year if claim.vehicle else 2019),
            "BasePolicy": base_policy
        }

        return data

    def process_claim(self, claim_id: str) -> Tuple[List[float], Dict[str, Any]]:
        start_time = datetime.utcnow()
        try:
            self._load_artifacts()
            raw_data = self._retrieve_claim_data(claim_id)
            
            df = pd.DataFrame([raw_data])
            
            # Use the exact preprocessing pipeline from training to transform raw data
            encoded_array = self.wrapper_pipeline.preprocessing_pipeline.transform(df)
            
            if hasattr(encoded_array, "toarray"):
                encoded_array = encoded_array.toarray()
                
            feature_vector = encoded_array[0].tolist()
            
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self._save_log(claim_id, "success", processing_time_ms)
            
            return feature_vector, {
                "status": "success",
                "processing_time_ms": processing_time_ms,
                "missing_values_imputed": self.logs["missing_values_imputed"],
                "features_engineered": self.logs["features_engineered"],
                "warnings": self.logs["warnings"],
                "errors": self.logs["errors"]
            }
            
        except Exception as e:
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            self.logs["errors"].append(str(e))
            self._save_log(claim_id, "failed", processing_time_ms)
            
            return [], {
                "status": "failed",
                "processing_time_ms": processing_time_ms,
                "missing_values_imputed": self.logs["missing_values_imputed"],
                "features_engineered": self.logs["features_engineered"],
                "warnings": self.logs["warnings"],
                "errors": self.logs["errors"]
            }

    def _save_log(self, claim_id: str, status: str, processing_time_ms: int):
        log_entry = models.PreprocessingLog(
            claim_id=claim_id,
            status=status,
            processing_time_ms=processing_time_ms,
            missing_values_imputed=self.logs["missing_values_imputed"],
            features_engineered=self.logs["features_engineered"],
            warnings=self.logs["warnings"],
            errors=self.logs["errors"]
        )
        self.db.add(log_entry)
        self.db.commit()
