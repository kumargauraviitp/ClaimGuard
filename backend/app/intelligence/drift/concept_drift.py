from sqlalchemy.orm import Session
from app.models import PredictionEvaluation
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any

class ConceptDriftMonitor:
    def __init__(self, db: Session):
        self.db = db
        
    def check_concept_drift(self, window_days: int = 30) -> Dict[str, Any]:
        """Check for concept drift by analyzing false positive/negative rates over time."""
        since_date = datetime.utcnow() - timedelta(days=window_days)
        
        # Get evaluations in the window
        evaluations = self.db.query(PredictionEvaluation).filter(PredictionEvaluation.reviewed_at >= since_date).all()
        
        if len(evaluations) < 10:
            return {"status": "insufficient_data"}
            
        total = len(evaluations)
        false_positives = sum(1 for e in evaluations if e.error_type == "FP")
        false_negatives = sum(1 for e in evaluations if e.error_type == "FN")
        true_positives = sum(1 for e in evaluations if e.error_type == "TP")
        
        fp_rate = false_positives / total
        fn_rate = false_negatives / total
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        
        drift_detected = (fp_rate > 0.15) or (fn_rate > 0.15) or (precision < 0.70)
        
        return {
            "status": "completed",
            "drift_detected": drift_detected,
            "metrics": {
                "total_evaluations": total,
                "fp_rate": float(fp_rate),
                "fn_rate": float(fn_rate),
                "precision": float(precision)
            }
        }
