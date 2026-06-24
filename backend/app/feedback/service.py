from sqlalchemy.orm import Session
from app.feedback.repository import FeedbackRepository
from app.feedback.schemas import FeedbackCreate
from typing import List
from uuid import UUID

class FeedbackService:
    def __init__(self, db: Session):
        self.repository = FeedbackRepository(db)

    def submit_feedback(self, investigator_id: UUID, data: FeedbackCreate):
        return self.repository.create_feedback(investigator_id, data)

    def get_history(self, skip: int = 0, limit: int = 100):
        return self.repository.get_feedback_history(skip, limit)
