from sqlalchemy.orm import Session
from app.models import Prediction
from typing import Dict, Any
from uuid import UUID

class DecisionSupportEngine:
    def __init__(self, db: Session):
        self.db = db
        
    def generate_recommendations(self, prediction_id: UUID) -> Dict[str, Any]:
        """Generate human-in-the-loop recommendations based on model confidence and intelligence."""
        prediction = self.db.query(Prediction).filter(Prediction.id == prediction_id).first()
        if not prediction:
            return {"status": "not_found"}
            
        prob = prediction.fraud_probability
        
        # Recommendations logic
        actions = []
        priority = "Low"
        
        if prob > 0.8:
            priority = "Critical"
            actions.extend([
                "Freeze claim payout immediately.",
                "Assign to Senior Fraud Investigator.",
                "Request additional digital evidence (photos, police reports)."
            ])
        elif prob > 0.5:
            priority = "High"
            actions.extend([
                "Flag for manual review.",
                "Verify vehicle and customer history for past claims.",
                "Cross-check witness statements."
            ])
        else:
            actions.extend([
                "Proceed with standard claim processing.",
                "No immediate fraud indicators detected."
            ])
            
        return {
            "prediction_id": str(prediction_id),
            "fraud_probability": prob,
            "priority": priority,
            "recommended_actions": actions,
            "human_review_required": prob > 0.5
        }
