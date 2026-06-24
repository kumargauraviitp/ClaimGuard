from sqlalchemy.orm import Session
from app.models import SecurityEvent, LoginHistory
from typing import Optional
import uuid

class AuditService:
    @staticmethod
    def log_security_event(
        db: Session,
        event_type: str,
        description: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Immutable append-only audit log.
        No updates or deletes are ever permitted on SecurityEvent.
        """
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(event)
        db.commit()

    @staticmethod
    def log_login_attempt(
        db: Session,
        username_attempted: str,
        success: bool,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        browser: Optional[str] = None,
        device: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> LoginHistory:
        
        history = LoginHistory(
            user_id=user_id,
            username_attempted=username_attempted,
            success=success,
            ip_address=ip_address,
            browser=browser,
            device=device,
            failure_reason=failure_reason
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
