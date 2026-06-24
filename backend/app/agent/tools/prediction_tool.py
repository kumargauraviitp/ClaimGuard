from sqlalchemy.orm import Session
from app.models import Prediction

def load_prediction(db: Session, claim_id: str) -> dict:
    pred = db.query(Prediction).filter(Prediction.claim_id == claim_id).first()
    if not pred:
        return {"fraud_probability": None, "risk_tier": "Unknown", "message": "No prediction run yet."}
    
    return {
        "fraud_probability": pred.fraud_probability,
        "is_fraud": pred.is_fraud,
        "risk_tier": pred.risk_tier,
        "timestamp": str(pred.created_at)
    }
