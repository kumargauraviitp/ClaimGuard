from sqlalchemy.orm import Session
from app.models import AgentAudit
import uuid

def log_audit_event(db: Session, claim_id: uuid.UUID, action: str, user_id: str = "system", details: dict = None):
    """
    Immutable audit trail logging. Append-only.
    """
    audit = AgentAudit(
        claim_id=claim_id,
        action=action,
        user_id=user_id,
        details=details or {}
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
