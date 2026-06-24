from sqlalchemy.orm import Session
from app.models import InvestigatorFeedback, PredictionEvaluation, CaseResolution, Prediction, Claim
from app.feedback.schemas import FeedbackCreate
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(self, investigator_id: UUID, data: FeedbackCreate) -> InvestigatorFeedback:
        # 1. Update Claim Status
        claim = self.db.query(Claim).filter(Claim.id == data.claim_id).first()
        if claim:
            claim.status = "investigated"

        # 2. Create Investigator Feedback
        feedback = InvestigatorFeedback(
            claim_id=data.claim_id,
            investigator_id=investigator_id,
            final_decision=data.final_decision,
            investigation_notes=data.investigation_notes,
            investigation_duration_hours=data.investigation_duration_hours
        )
        self.db.add(feedback)

        # 2. Update Prediction Evaluation
        prediction = self.db.query(Prediction).filter(Prediction.id == data.prediction_id).first()
        if prediction:
            ground_truth = 1 if data.fraud_confirmed else 0
            predicted_label = 1 if prediction.fraud_probability >= 0.5 else 0 # Or use dynamic threshold
            
            is_correct = (ground_truth == predicted_label)
            if ground_truth == 1 and predicted_label == 1:
                error_type = "TP"
            elif ground_truth == 0 and predicted_label == 0:
                error_type = "TN"
            elif ground_truth == 0 and predicted_label == 1:
                error_type = "FP"
            else:
                error_type = "FN"

            evaluation = PredictionEvaluation(
                prediction_id=data.prediction_id,
                ground_truth=ground_truth,
                predicted_label=predicted_label,
                is_correct=is_correct,
                error_type=error_type,
                reviewed_by=investigator_id,
                reviewed_at=datetime.utcnow()
            )
            self.db.add(evaluation)

        # 3. Create Case Resolution
        resolution = CaseResolution(
            claim_id=data.claim_id,
            fraud_confirmed=data.fraud_confirmed,
            claim_approved=data.claim_approved
        )
        self.db.add(resolution)

        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_feedback_history(self, skip: int = 0, limit: int = 100) -> List[InvestigatorFeedback]:
        return self.db.query(InvestigatorFeedback).order_by(InvestigatorFeedback.timestamp.desc()).offset(skip).limit(limit).all()
