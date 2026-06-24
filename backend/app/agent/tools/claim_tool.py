from sqlalchemy.orm import Session
from app.models import Claim

def load_claim(db: Session, claim_id: str) -> dict:
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ValueError(f"Claim {claim_id} not found")
    
    # Simple dict dump
    return {
        "id": str(claim.id),
        "policy_id": str(claim.policy_id),
        "claim_number": claim.claim_number,
        "filing_date": str(claim.filing_date),
        "status": claim.status,
        # In a real app we would join Customer, Vehicle, Policy here.
    }
