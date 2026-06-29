from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role, Permission, APIKey, Claim
from app.auth.jwt_service import JWTService
from typing import List, Optional

security = HTTPBearer(auto_error=False)

def get_current_user_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency to resolve the current user or service account via API key.
    """
    if not credentials:
        # Check if an API key is provided via header
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            import hashlib
            key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
            api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
            if not api_key:
                raise HTTPException(status_code=401, detail="Invalid API Key")
            from datetime import datetime
            api_key.last_used = datetime.utcnow()
            db.commit()
            
            # Create a mock user object representing the service account
            class ServiceAccount:
                id = api_key.id
                username = f"service_{api_key.name}"
                is_service_account = True
                roles = []
                permissions = ["*"] # Service accounts are typically superusers or heavily restricted by specific scopes (not implemented in this PoC)
            return ServiceAccount()
            
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    payload = JWTService.verify_token(token, db)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    if user.status != "Active":
        raise HTTPException(status_code=403, detail="Account is not active")
        
    if user.force_password_change:
        if request.url.path not in ["/auth/change-password", "/auth/logout", "/auth/me"]:
            raise HTTPException(status_code=403, detail="Password change required")
            
    setattr(user, "is_service_account", False)
    return user

class RequirePermissions:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def __call__(self, user = Depends(get_current_user_or_api_key), db: Session = Depends(get_db)):
        if getattr(user, "is_service_account", False):
            # Service account bypasses RBAC in this PoC
            return user
            
        # Get all user permissions
        user_perms = set()
        for role in user.roles:
            for perm in role.permissions:
                user_perms.add(perm.name)
                
        # Superuser shortcut
        if "*" in user_perms:
            return user
            
        # Check required permissions
        for rp in self.required_permissions:
            if rp not in user_perms:
                raise HTTPException(status_code=403, detail=f"Missing permission: {rp}")
                
        return user

class ABACPolicy:
    """
    Attribute-Based Access Control and Resource Ownership.
    """
    @staticmethod
    def verify_claim_ownership(claim_id: str, user, db: Session) -> None:
        if getattr(user, "is_service_account", False):
            return
            
        # If user is admin/manager, allow all
        user_roles = [r.name for r in user.roles]
        if "Admin" in user_roles or "Claims Manager" in user_roles:
            return
            
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        # Row-level security / Ownership check
        # Example: Investigators can only view claims assigned to them
        # Note: We fetch the investigation record associated with the claim
        from app.models import Investigation
        inv = db.query(Investigation).filter(Investigation.claim_id == claim_id).first()
        if inv and inv.investigator_id != str(user.id):
            raise HTTPException(status_code=403, detail="You do not own this claim.")
