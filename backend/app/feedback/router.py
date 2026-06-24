from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.router import get_current_user_or_api_key
from app.models import User
from app.feedback.schemas import FeedbackCreate, FeedbackResponse
from app.feedback.service import FeedbackService

router = APIRouter(prefix="/api/feedback", tags=["Investigator Feedback"])

@router.post("/submit", response_model=FeedbackResponse)
def submit_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key)
):
    """Submit investigator feedback and update ground truth/evaluation."""
    try:
        if isinstance(current_user, dict):
            investigator_id = None
        else:
            investigator_id = current_user.id
            
        service = FeedbackService(db)
        feedback = service.submit_feedback(investigator_id, data)
        return feedback
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error submitting feedback: {str(e)}")


@router.get("/history", response_model=List[FeedbackResponse])
def get_feedback_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key)
):
    """Retrieve history of all investigator feedback."""
    service = FeedbackService(db)
    return service.get_history(skip, limit)
