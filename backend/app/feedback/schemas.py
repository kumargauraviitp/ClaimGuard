from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class FeedbackCreate(BaseModel):
    claim_id: str
    prediction_id: UUID
    final_decision: str = Field(..., description="e.g., Fraud Confirmed, Genuine Claim")
    investigation_notes: Optional[str] = None
    investigation_duration_hours: Optional[float] = None
    
    # Ground truth for prediction evaluation
    fraud_confirmed: bool
    claim_approved: bool

class FeedbackResponse(BaseModel):
    id: UUID
    claim_id: UUID
    investigator_id: Optional[UUID]
    final_decision: str
    investigation_notes: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
