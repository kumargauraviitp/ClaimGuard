from sqlalchemy.orm import Session
from app.models import ModelExplanation

def load_shap(db: Session, claim_id: str) -> dict:
    exp = db.query(ModelExplanation).filter(ModelExplanation.claim_id == claim_id).first()
    if not exp:
        return {"message": "No SHAP explanation found."}
        
    return {
        "top_positive_features": exp.top_positive_features,
        "top_negative_features": exp.top_negative_features,
        "base_value": exp.base_value,
        "prediction_value": exp.prediction_value
    }
