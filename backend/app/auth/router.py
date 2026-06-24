from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role, Permission
from app.auth import schemas
from app.auth.schemas import (
    LoginRequest, LoginResponse, RegisterRequest, ChangePasswordRequest, 
    RefreshTokenRequest, UserResponse, RoleCreate, PermissionAssign, MFASetupResponse, MFAVerifyRequest
)
from app.auth.auth_service import AuthService
from app.auth.password_service import PasswordService
from app.auth.jwt_service import JWTService
from app.auth.session_service import SessionService
from app.auth.permission_service import RequirePermissions, get_current_user_or_api_key
from app.auth.mfa_service import MFAService
from app.auth.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])

@router.post("/login", response_model=LoginResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    auth_svc = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    result = auth_svc.authenticate_user(
        username=payload.username, 
        password=payload.password, 
        mfa_code=payload.mfa_code,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return result

@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    from app.models import Customer
    from sqlalchemy.exc import IntegrityError
    # Check if user exists
    existing = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Also check if a customer with this email already exists
    existing_customer = db.query(Customer).filter(Customer.email == payload.email).first()
        
    try:
        PasswordService.validate_password_policy(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    password_hash = PasswordService.get_password_hash(payload.password)
    
    # Create Customer Profile (or reuse existing one)
    first_name = payload.full_name.split()[0] if " " in payload.full_name else payload.full_name
    last_name = payload.full_name.split(" ", 1)[1] if " " in payload.full_name else ""
    
    parsed_dob = None
    if payload.dob:
        try:
            parsed_dob = datetime.strptime(payload.dob, "%Y-%m-%d")
        except ValueError:
            pass

    try:
        if existing_customer:
            # Reuse the existing customer record
            new_customer = existing_customer
            new_customer.first_name = first_name
            new_customer.last_name = last_name
            new_customer.phone = payload.phone
            new_customer.age = payload.age
            new_customer.date_of_birth = parsed_dob
        else:
            new_customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=payload.email,
                phone=payload.phone,
                age=payload.age,
                date_of_birth=parsed_dob
            )
            db.add(new_customer)
            db.flush()
        
        new_user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            password_hash=password_hash,
            phone=payload.phone,
            status="Active",  # Auto-activate for ease of use
            force_password_change=False,
            customer_id=new_customer.id
        )
        
        # Assign Customer role
        customer_role = db.query(Role).filter(Role.name == "Customer").first()
        if customer_role:
            new_user.roles.append(customer_role)
            
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        AuditService.log_security_event(db, "user_registered", "New customer registered via signup", new_user.id)
        return {"status": "success", "message": "User registered successfully"}
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "email" in error_msg.lower():
            raise HTTPException(status_code=400, detail="This email is already registered")
        elif "username" in error_msg.lower():
            raise HTTPException(status_code=400, detail="This username is already taken")
        else:
            raise HTTPException(status_code=400, detail="Registration failed. Please try different credentials.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user_or_api_key)):
    # Extract access token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
        JWTService.revoke_token(db, access_token)
        
    SessionService.revoke_all_user_sessions(db, str(current_user.id))
    AuditService.log_security_event(db, "logout", "User logged out", current_user.id)
    return {"status": "success", "message": "Logged out successfully"}

@router.post("/refresh", response_model=LoginResponse)
def refresh_token(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    if not SessionService.validate_refresh_token(db, payload.refresh_token):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    verified = JWTService.verify_token(payload.refresh_token, db, expected_type="refresh")
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    # In a real system, you'd generate a NEW access token and return it.
    # Optionally, generate a new refresh token (Refresh Token Rotation).
    # SessionService.revoke_refresh_token(db, payload.refresh_token) # Disabled to prevent race conditions in SPA
    
    user = db.query(User).filter(User.id == verified["sub"]).first()
    if not user or user.status != "Active":
        raise HTTPException(status_code=401, detail="User inactive")
        
    # Recreate payload
    roles = [r.name for r in user.roles]
    perms = list(set([p.name for r in user.roles for p in r.permissions]))
    new_payload = {
        "sub": str(user.id),
        "username": user.username,
        "roles": roles,
        "permissions": perms,
        "force_password_change": user.force_password_change
    }
    
    access_token = JWTService.create_access_token(new_payload)
    new_refresh_token = JWTService.create_refresh_token(new_payload)
    
    from app.auth.secrets_manager import REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    SessionService.register_refresh_token(db, user, new_refresh_token, expires_at)
    
    return {
        "tokens": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        },
        "requires_mfa": False,
        "mfa_setup_required": False
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user = Depends(get_current_user_or_api_key)):
    # Convert ORM to expected Pydantic model implicitly
    # Add roles and permissions
    if getattr(current_user, "is_service_account", False):
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": "service@internal.local",
            "full_name": current_user.username,
            "roles": [],
            "permissions": ["*"],
            "status": "Active",
            "mfa_enabled": False,
            "force_password_change": False,
            "last_login": None
        }
        
    roles = [r.name for r in current_user.roles]
    perms = list(set([p.name for r in current_user.roles for p in r.permissions]))
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": roles,
        "permissions": perms,
        "status": current_user.status,
        "mfa_enabled": current_user.mfa_enabled,
        "force_password_change": current_user.force_password_change,
        "phone": current_user.phone,
        "customer_id": current_user.customer_id,
        "last_login": current_user.last_login
    }

from pydantic import BaseModel
class ProfileUpdateRequest(BaseModel):
    full_name: str
    phone: str
    age: int
    dob: str

@router.put("/me")
def update_current_user_profile(payload: ProfileUpdateRequest, current_user = Depends(get_current_user_or_api_key), db: Session = Depends(get_db)):
    from app.models import Customer
    if getattr(current_user, "is_service_account", False):
        raise HTTPException(status_code=400, detail="Service accounts cannot update profile.")
        
    current_user.full_name = payload.full_name
    current_user.phone = payload.phone
    db.commit()
    
    if current_user.customer_id:
        customer = db.query(Customer).filter(Customer.id == current_user.customer_id).first()
        if customer:
            first_name = payload.full_name.split()[0] if " " in payload.full_name else payload.full_name
            last_name = payload.full_name.split(" ", 1)[1] if " " in payload.full_name else ""
            customer.first_name = first_name
            customer.last_name = last_name
            customer.phone = payload.phone
            customer.age = payload.age
            try:
                customer.date_of_birth = datetime.strptime(payload.dob, "%Y-%m-%d")
            except ValueError:
                pass
            db.commit()
            
    return {"status": "success", "message": "Profile updated"}

@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user_or_api_key)):
    if getattr(current_user, "is_service_account", False):
        raise HTTPException(status_code=400, detail="Service accounts cannot change passwords.")
        
    if not PasswordService.verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    PasswordService.validate_password_policy(payload.new_password)
    PasswordService.check_password_history(db, current_user, payload.new_password)
    
    new_hash = PasswordService.get_password_hash(payload.new_password)
    current_user.password_hash = new_hash
    current_user.force_password_change = False
    db.commit()
    
    PasswordService.add_to_history(db, str(current_user.id), new_hash)
    
    AuditService.log_security_event(db, "password_changed", "User changed their password", current_user.id)
    return {"status": "success", "message": "Password updated successfully."}

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(current_user = Depends(get_current_user_or_api_key), db: Session = Depends(get_db)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled.")
        
    secret = MFAService.generate_secret()
    current_user.mfa_secret = secret
    db.commit()
    
    uri = MFAService.get_provisioning_uri(secret, current_user.email)
    return MFASetupResponse(secret=secret, provisioning_uri=uri)

@router.post("/mfa/verify")
def verify_mfa_setup(payload: MFAVerifyRequest, current_user = Depends(get_current_user_or_api_key), db: Session = Depends(get_db)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled.")
        
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="Call /mfa/setup first.")
        
    if MFAService.verify_totp(current_user.mfa_secret, payload.code):
        current_user.mfa_enabled = True
        db.commit()
        AuditService.log_security_event(db, "mfa_enabled", "User successfully set up MFA", current_user.id)
        return {"status": "success", "message": "MFA enabled successfully."}
    else:
        raise HTTPException(status_code=400, detail="Invalid MFA code.")

# User Management (Admin Only)
@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user = Depends(RequirePermissions(["user.read"]))):
    users = db.query(User).all()
    res = []
    for u in users:
        res.append({
            "id": u.id, "username": u.username, "email": u.email, 
            "status": u.status, "roles": [r.name for r in u.roles]
        })
    return res

@router.post("/users/{user_id}/status")
def change_user_status(user_id: str, status: str, db: Session = Depends(get_db), current_user = Depends(RequirePermissions(["user.update"]))):
    valid_statuses = ["Active", "Suspended", "Archived", "Deleted"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.status = status
    db.commit()
    AuditService.log_security_event(db, "user_status_changed", f"User {user.username} status changed to {status} by {current_user.username}", user.id)
    return {"status": "success", "message": f"User status updated to {status}"}

@router.get("/events")
def list_security_events(limit: int = 50, db: Session = Depends(get_db), current_user = Depends(RequirePermissions(["security.read"]))):
    from app.models import SecurityEvent
    from sqlalchemy import desc
    events = db.query(SecurityEvent).order_by(desc(SecurityEvent.timestamp)).limit(limit).all()
    return events

# ---------------------------------------------------------
# API Key Management (Admin only)
# ---------------------------------------------------------

@router.post("/api-keys", response_model=schemas.APIKeyCreateResponse)
def create_api_key(payload: schemas.APIKeyCreate, db: Session = Depends(get_db), current_user = Depends(RequirePermissions(["security.write"]))):
    import secrets
    import hashlib
    from app.models import APIKey
    
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = APIKey(name=payload.name, key_hash=key_hash)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    AuditService.log_security_event(db, "api_key_created", f"API Key '{payload.name}' created by {current_user.username}")
    
    return schemas.APIKeyCreateResponse(api_key=api_key, raw_key=raw_key)

@router.get("/api-keys", response_model=List[schemas.APIKeyResponse])
def list_api_keys(db: Session = Depends(get_db), current_user = Depends(RequirePermissions(["security.read"]))):
    from app.models import APIKey
    return db.query(APIKey).all()

@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: str, db: Session = Depends(get_db), current_user = Depends(RequirePermissions(["security.write"]))):
    from app.models import APIKey
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    api_key.is_active = False
    db.commit()
    AuditService.log_security_event(db, "api_key_revoked", f"API Key '{api_key.name}' revoked by {current_user.username}")
    return {"status": "success", "message": "API Key revoked"}
