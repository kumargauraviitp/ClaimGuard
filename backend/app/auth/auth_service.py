from sqlalchemy.orm import Session
from app.models import User
from app.auth.password_service import PasswordService
from app.auth.jwt_service import JWTService
from app.auth.session_service import SessionService
from app.auth.security_service import SecurityService
from app.auth.audit_service import AuditService
from app.auth.mfa_service import MFAService
from fastapi import HTTPException
from datetime import datetime, timedelta

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, username: str, password: str, mfa_code: str = None, ip_address: str = None, user_agent: str = None):
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            AuditService.log_login_attempt(self.db, username, False, None, ip_address, None, user_agent, "User not found")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if user.status != "Active":
            AuditService.log_login_attempt(self.db, username, False, user.id, ip_address, None, user_agent, "Account inactive")
            raise HTTPException(status_code=403, detail="Account is not active")

        if SecurityService.is_account_locked(user):
            AuditService.log_login_attempt(self.db, username, False, user.id, ip_address, None, user_agent, "Account locked")
            raise HTTPException(status_code=403, detail="Account is locked. Try again later.")

        if not PasswordService.verify_password(password, user.password_hash):
            SecurityService.handle_failed_login(self.db, user, ip_address, user_agent)
            AuditService.log_login_attempt(self.db, username, False, user.id, ip_address, None, user_agent, "Invalid password")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if user.mfa_enabled:
            if not mfa_code:
                # Login step 1 completed, need MFA
                return {"requires_mfa": True}
            if not MFAService.verify_totp(user.mfa_secret, mfa_code):
                SecurityService.handle_failed_login(self.db, user, ip_address, user_agent)
                AuditService.log_login_attempt(self.db, username, False, user.id, ip_address, None, user_agent, "Invalid MFA code")
                raise HTTPException(status_code=401, detail="Invalid MFA code")

        # Success!
        SecurityService.handle_successful_login(self.db, user)
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Build payload
        roles = [r.name for r in user.roles]
        perms = []
        for r in user.roles:
            perms.extend([p.name for p in r.permissions])
            
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "roles": roles,
            "permissions": list(set(perms)),
            "force_password_change": user.force_password_change
        }
        
        access_token = JWTService.create_access_token(payload)
        refresh_token = JWTService.create_refresh_token(payload)
        
        from app.auth.secrets_manager import REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        SessionService.register_refresh_token(self.db, user, refresh_token, expires_at)
        
        AuditService.log_login_attempt(self.db, username, True, user.id, ip_address, None, user_agent)
        
        return {
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            },
            "requires_mfa": False,
            "mfa_setup_required": False
        }
