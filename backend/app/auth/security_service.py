from sqlalchemy.orm import Session
from app.models import User
from app.auth.audit_service import AuditService
from datetime import datetime, timedelta

class SecurityService:
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    @staticmethod
    def handle_failed_login(db: Session, user: User, ip_address: str = None, user_agent: str = None) -> None:
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= SecurityService.MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=SecurityService.LOCKOUT_DURATION_MINUTES)
            AuditService.log_security_event(
                db=db,
                event_type="account_locked",
                description=f"Account locked due to {SecurityService.MAX_FAILED_ATTEMPTS} failed attempts.",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
        db.commit()

    @staticmethod
    def handle_successful_login(db: Session, user: User) -> None:
        if user.failed_login_attempts > 0 or user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

    @staticmethod
    def is_account_locked(user: User) -> bool:
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
