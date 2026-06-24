from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Claim, InvestigatorFeedback
from uuid import UUID

class FraudNetworkAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def find_linked_fraud_cases(self, claim_id: UUID) -> Dict[str, Any]:
        """
        Identifies potential fraud rings by looking for shared attributes 
        (e.g., same customer, same vehicle) among confirmed fraud cases.
        """
        # Get the target claim
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return {"status": "not_found"}

        # Find other claims by the same customer or involving the same vehicle
        linked_claims = self.db.query(Claim).filter(
            (Claim.customer_id == claim.customer_id) | 
            (Claim.vehicle_id == claim.vehicle_id)
        ).filter(Claim.id != claim_id).all()

        linked_fraud_count = 0
        nodes = [{"id": str(claim.id), "type": "target", "fraud_confirmed": None}]
        edges = []

        for lc in linked_claims:
            # Check if this linked claim was confirmed as fraud
            feedback = self.db.query(InvestigatorFeedback).filter(
                InvestigatorFeedback.claim_id == lc.id,
                InvestigatorFeedback.final_decision == "Fraud Confirmed"
            ).first()
            
            is_fraud = feedback is not None
            if is_fraud:
                linked_fraud_count += 1
                
            nodes.append({
                "id": str(lc.id),
                "type": "linked_claim",
                "fraud_confirmed": is_fraud
            })
            
            # Add edges
            if lc.customer_id == claim.customer_id:
                edges.append({"source": str(claim.id), "target": str(lc.id), "relation": "same_customer"})
            if lc.vehicle_id == claim.vehicle_id:
                edges.append({"source": str(claim.id), "target": str(lc.id), "relation": "same_vehicle"})

        risk_level = "High" if linked_fraud_count > 0 else "Low"

        return {
            "status": "completed",
            "network_risk_level": risk_level,
            "linked_fraud_cases": linked_fraud_count,
            "network": {
                "nodes": nodes,
                "edges": edges
            }
        }
