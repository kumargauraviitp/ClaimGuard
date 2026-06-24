"""
Fraud Rule Engine — runs AFTER the ML model produces its base probability.

Applies deterministic hard rules that MODIFY the ML probability using
a Bayesian multiplicative model.  Each rule reduces the "not-fraud"
probability (1 - p), so rules compound with diminishing returns —
they boost risk but can never balloon a low score to 99% on their own.

  final = 1 - (1 - base_ml_prob) * ∏(1 - score_added_i)

Rule scores represent the "fraction of remaining innocence removed":
- Invalid policy/registration (not in whitelist) → removes 35% of remaining innocence
- No police FIR filed → removes 12%
- Missing mandatory data → removes 8% per field
- Suspicious/wrong data values → removes 10% per anomaly
- No witnesses → removes 5%
- Injured but no medical expenses → removes 8%
- Junk/unrelated documents → removes 20%

Band-pinning rule (both/single invalid policy-or-vehicle) assigns a value
WITHIN the band that is DETERMINISTIC per claim — derived from a hash of
the claim id — so rescanning the same claim always returns the same score,
while different claims still show varied scores across the band.
"""
import hashlib
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import (
    Claim, Customer, Vehicle, Policy, Accident,
    FinancialDetails, PoliceDetails, Witness, Document,
    Prediction,
)
from app.fraud_rules.reference_lists import is_valid_policy, is_valid_vehicle


def _deterministic_in_band(claim_id: str, lo: float, hi: float) -> float:
    """Return a stable pseudo-random float in [lo, hi) for a given claim id.

    Uses an MD5 hash of the claim id so the SAME claim ALWAYS yields the
    SAME value across rescans (no flapping), but DIFFERENT claims spread
    across the band instead of all landing on a single flat value.
    """
    h = hashlib.md5(str(claim_id).encode("utf-8")).hexdigest()
    # Take the first 8 hex chars -> 32-bit int -> fraction in [0, 1)
    frac = int(h[:8], 16) / 0xFFFFFFFF
    return lo + frac * (hi - lo)


# Each flag: {rule, label, reason (human-readable), score_added}
Flag = Dict[str, Any]


class FraudRuleEngine:
    def __init__(self, db: Session, claim_id: str):
        self.db = db
        self.claim_id = claim_id
        self._claim = None
        self._customer = None
        self._vehicle = None
        self._policy = None
        self._accident = None
        self._financials = None
        self._police = None
        self._witnesses = None
        self._documents = None
        self._predictions = None

    # ---------- Lazy loaders ----------
    @property
    def claim(self) -> Optional[Claim]:
        if not self._claim:
            self._claim = self.db.query(Claim).filter(Claim.id == self.claim_id).first()
        return self._claim

    @property
    def customer(self) -> Optional[Customer]:
        if not self._customer and self.claim:
            self._customer = self.db.query(Customer).filter(Customer.id == self.claim.customer_id).first()
        return self._customer

    @property
    def vehicle(self) -> Optional[Vehicle]:
        if not self._vehicle and self.claim:
            self._vehicle = self.db.query(Vehicle).filter(Vehicle.id == self.claim.vehicle_id).first()
        return self._vehicle

    @property
    def policy(self) -> Optional[Policy]:
        if not self._policy and self.claim:
            self._policy = self.db.query(Policy).filter(Policy.id == self.claim.policy_id).first()
        return self._policy

    @property
    def accident(self) -> Optional[Accident]:
        if not self._accident and self.claim:
            self._accident = self.db.query(Accident).filter(Accident.claim_id == self.claim.id).first()
        return self._accident

    @property
    def financials(self) -> Optional[FinancialDetails]:
        if not self._financials and self.claim:
            self._financials = self.db.query(FinancialDetails).filter(
                FinancialDetails.claim_id == self.claim.id
            ).first()
        return self._financials

    @property
    def police(self) -> Optional[PoliceDetails]:
        if not self._police and self.claim:
            self._police = self.db.query(PoliceDetails).filter(
                PoliceDetails.claim_id == self.claim.id
            ).first()
        return self._police

    @property
    def witnesses(self) -> List[Witness]:
        if self._witnesses is None and self.claim:
            self._witnesses = self.db.query(Witness).filter(
                Witness.claim_id == self.claim.id
            ).all()
        return self._witnesses or []

    @property
    def documents(self) -> List[Document]:
        if self._documents is None and self.claim:
            self._documents = self.db.query(Document).filter(
                Document.claim_id == self.claim.id
            ).all()
        return self._documents or []

    # ---------- Individual rule checks ----------

    def _check_invalid_policy(self, flags: List[Flag]):
        """Policy number not in the known whitelist."""
        if not self.policy:
            return
        pn = self.policy.policy_number
        # Skip auto-generated policy numbers (they start with POL- followed by hex)
        if pn and re.match(r'^POL-[A-F0-9]{8}$', pn.strip()):
            flags.append({
                "rule": "INVALID_POLICY",
                "label": "⚠ Unregistered policy number",
                "reason": f"The policy number '{pn}' is not in our records. "
                          f"This could mean the policy was fabricated for this claim.",
                "score_added": 0.35,
            })
            return
        if pn and not is_valid_policy(self.db, pn):
            flags.append({
                "rule": "INVALID_POLICY",
                "label": "⚠ Unregistered policy number",
                "reason": f"The policy number '{pn}' is not in our system's records. "
                          f"Claims must reference a valid, active insurance policy.",
                "score_added": 0.35,
            })

    def _check_invalid_vehicle(self, flags: List[Flag]):
        """Vehicle registration plate not in the known whitelist."""
        if not self.vehicle:
            return
        lp = self.vehicle.license_plate
        # Skip auto-generated (UNKNOWN or VIN-xxx)
        if not lp or lp == "UNKNOWN" or lp.startswith("VIN"):
            flags.append({
                "rule": "INVALID_VEHICLE",
                "label": "⚠ Unregistered vehicle",
                "reason": "No valid vehicle registration number was provided. "
                          "The vehicle cannot be verified in our records.",
                "score_added": 0.35,
            })
            return
        if not is_valid_vehicle(self.db, lp):
            flags.append({
                "rule": "INVALID_VEHICLE",
                "label": "⚠ Unregistered vehicle",
                "reason": f"The registration number '{lp}' is not found in our vehicle database. "
                          f"This may indicate a fake or stolen vehicle plate.",
                "score_added": 0.35,
            })

    def _check_no_fir(self, flags: List[Flag]):
        """No police FIR filed for the accident."""
        if not self.police:
            return
        if not self.police.police_report_available:
            flags.append({
                "rule": "NO_FIR",
                "label": "⚠ No police report filed",
                "reason": "No police FIR has been filed for this accident. "
                          "Legitimate accidents typically involve a police report, especially "
                          "for claims involving vehicle damage or injury.",
                "score_added": 0.12,
            })

    def _check_fir_but_no_number(self, flags: List[Flag]):
        """Said FIR was filed but no FIR number provided."""
        if not self.police:
            return
        if self.police.police_report_available and not self.police.fir_number:
            flags.append({
                "rule": "NO_FIR_BUT_CLAIMED",
                "label": "⚠ FIR claimed but no number",
                "reason": "The claimant says a police report was filed, but no FIR number "
                          "was provided. This inconsistency is a red flag.",
                "score_added": 0.15,
            })

    def _check_missing_data(self, flags: List[Flag]):
        """Mandatory fields are empty or missing."""
        if not self.customer or not self.claim:
            return

        missing = []
        c = self.customer
        if not c.first_name or c.first_name == "Unknown":
            missing.append("customer name")
        if not c.phone:
            missing.append("phone number")
        if not c.city:
            missing.append("city/address")

        if self.accident:
            if not self.accident.incident_date:
                missing.append("incident date")
            if not self.accident.accident_description:
                missing.append("accident description")

        if self.financials and (not self.financials.claim_amount or self.financials.claim_amount == 0):
            missing.append("claim amount")

        for field_name in missing:
            flags.append({
                "rule": "MISSING_DATA",
                "label": f"⚠ Missing: {field_name}",
                "reason": f"The {field_name} was not provided. Incomplete claims are "
                          f"often associated with fraudulent submissions.",
                "score_added": 0.08,
            })

    def _check_wrong_data(self, flags: List[Flag]):
        """Detect suspicious or logically impossible values."""
        anomalies = []

        if self.customer:
            if self.customer.age and self.customer.age < 18:
                anomalies.append(
                    f"The customer's age is {self.customer.age}, which is below the "
                    f"legal driving age of 18."
                )

        if self.accident:
            if self.accident.incident_date:
                try:
                    from datetime import datetime as _dt
                    raw = self.accident.incident_date
                    if isinstance(raw, _dt):
                        inc_date = raw.date()
                    elif hasattr(raw, 'year') and hasattr(raw, 'month') and hasattr(raw, 'day') and not isinstance(raw, _dt):
                        inc_date = raw  # already a date object
                    else:
                        inc_date = _dt.strptime(str(raw)[:10], "%Y-%m-%d").date()
                    if inc_date > date.today():
                        anomalies.append(
                            "The accident date is in the future, which is impossible."
                        )
                except (ValueError, TypeError):
                    anomalies.append("The accident date format is invalid.")

            if self.accident.vehicle_speed:
                if self.accident.vehicle_speed > 300:
                    anomalies.append(
                        f"The reported vehicle speed was {self.accident.vehicle_speed} km/h, "
                        f"which is unrealistically high for a normal road accident."
                    )

        if self.financials:
            if self.claim and self.claim.reporting_delay_days:
                if self.claim.reporting_delay_days > 180:
                    anomalies.append(
                        f"The accident was reported {self.claim.reporting_delay_days} days "
                        f"after it happened. Legitimate claims are usually filed within a few days."
                    )

        for reason in anomalies:
            flags.append({
                "rule": "WRONG_DATA",
                "label": "⚠ Suspicious data",
                "reason": reason,
                "score_added": 0.10,
            })

    def _check_no_witness(self, flags: List[Flag]):
        """No witnesses for the accident."""
        if len(self.witnesses) == 0:
            flags.append({
                "rule": "NO_WITNESS",
                "label": "⚠ No witnesses",
                "reason": "No witnesses were reported for this accident. "
                          "While not definitive, claims without witnesses are harder to verify.",
                "score_added": 0.05,
            })

    def _check_injured_no_medical(self, flags: List[Flag]):
        """People were injured but no medical expenses claimed."""
        if not self.accident or not self.financials:
            return
        injured = self.accident.number_of_injured or 0
        medical = self.financials.medical_expenses or 0
        hospital = self.financials.hospital_charges or 0
        if injured > 0 and medical == 0 and hospital == 0:
            flags.append({
                "rule": "NO_MEDICAL_BUT_INJURY",
                "label": "⚠ Injured but no medical expenses",
                "reason": f"The claim reports {injured} injured person(s), but no medical "
                          f"expenses or hospital charges were claimed. This is unusual.",
                "score_added": 0.08,
            })

    def _check_document_flags(self, flags: List[Flag]):
        """Check uploaded documents for verification status."""
        for doc in self.documents:
            status = getattr(doc, 'verification_status', None)
            doc_type = getattr(doc, 'document_type', None) or 'unknown'
            if status == "verified":
                continue  # Document is fine, no flag
            elif status == "rejected":
                flags.append({
                    "rule": "JUNK_DOCUMENT",
                    "label": "⚠ Unrelated document detected",
                    "reason": f"The uploaded document ('{doc_type}') was analyzed and found "
                              f"to be unrelated to this insurance claim. This is a strong fraud indicator.",
                    "score_added": 0.20,
                })
            elif status == "suspicious":
                flags.append({
                    "rule": "JUNK_DOCUMENT",
                    "label": "⚠ Suspicious document detected",
                    "reason": f"The uploaded document ('{doc_type}') could not be fully verified "
                              f"and may not be legitimate.",
                    "score_added": 0.15,
                })
            elif status == "unverified" or status is None:
                flags.append({
                    "rule": "UNVERIFIED_DOCUMENT",
                    "label": "⚠ Unverified document",
                    "reason": f"A document ('{doc_type}') was uploaded but has not been verified. "
                              f"Documents cannot be taken at face value without verification.",
                    "score_added": 0.10,
                })

    def _check_ai_validated_data(self, flags: List[Flag]):
        """Use AI to validate customer data (name, email, phone consistency)."""
        if not self.customer:
            return
        try:
            from app.explainability.ai_explainer import validate_customer_data
            anomalies = validate_customer_data(
                name=f"{self.customer.first_name or ''} {self.customer.last_name or ''}".strip(),
                email=self.customer.email or "",
                phone=self.customer.phone or "",
                age=self.customer.age,
                occupation=self.customer.occupation,
                city=self.customer.city,
            )
            flags.extend(anomalies)
        except Exception as e:
            print(f"AI customer validation failed: {e}")

    # ---------- Main evaluate method ----------

    def evaluate(self, base_ml_probability: float) -> Tuple[float, List[Flag]]:
        """
        Run all rules against the claim and return:
        - adjusted_probability: Bayesian multiplicative combination
        - flags: list of triggered rule flags with human-readable explanations

        Each triggered rule reduces the remaining "not-fraud" probability.
        This means rules compound with diminishing returns rather than
        adding up and ballooning past 99%.

            final = 1 - (1 - base) * ∏(1 - score_i)
        """
        if not self.claim:
            return base_ml_probability, []

        flags: List[Flag] = []

        # Run all rule checks
        self._check_invalid_policy(flags)
        self._check_invalid_vehicle(flags)
        self._check_no_fir(flags)
        self._check_fir_but_no_number(flags)
        self._check_missing_data(flags)
        self._check_wrong_data(flags)
        self._check_no_witness(flags)
        self._check_injured_no_medical(flags)
        self._check_document_flags(flags)
        self._check_ai_validated_data(flags)

        # Bayesian multiplicative combination: each rule reduces the
        # remaining innocence (1 - p) by its score fraction.
        innocence = 1.0 - base_ml_probability
        for f in flags:
            innocence *= (1.0 - f["score_added"])
        adjusted = 1.0 - innocence

        # Hardcoded rule: If both policy and vehicle registration are invalid,
        # force probability into the 85–95% Critical band. The value within the
        # band is DETERMINISTIC per claim (hash of claim id), so rescanning the
        # same claim always yields the same score — it only changes when the
        # underlying data genuinely changes and the rules/model re-detect it.
        has_invalid_policy = any(f["rule"] == "INVALID_POLICY" for f in flags)
        has_invalid_vehicle = any(f["rule"] == "INVALID_VEHICLE" for f in flags)
        if has_invalid_policy and has_invalid_vehicle:
            if adjusted < 0.85:
                adjusted = _deterministic_in_band(self.claim_id, 0.85, 0.95)
            flags.append({
                "rule": "CRITICAL_MISMATCH",
                "label": "🚨 Critical mismatch",
                "reason": "Both the policy number and vehicle registration are invalid. Fraud probability automatically elevated to the 85–95% Critical band.",
                "score_added": 0.0
            })
        elif has_invalid_policy or has_invalid_vehicle:
            if adjusted < 0.70:
                adjusted = _deterministic_in_band(self.claim_id, 0.70, 0.80)
            flags.append({
                "rule": "PARTIAL_MISMATCH",
                "label": "⚠️ Partial mismatch",
                "reason": "Either the policy number or the vehicle registration is invalid. Fraud probability automatically elevated to the 70–80% High band.",
                "score_added": 0.0
            })

        # Cap at 0.99 to leave room for human discretion
        adjusted = min(0.99, adjusted)

        return adjusted, flags
