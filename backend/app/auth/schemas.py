from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    tokens: TokenPair
    requires_mfa: bool = False
    mfa_setup_required: bool = False

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str

class MFAVerifyRequest(BaseModel):
    code: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    phone: Optional[str] = None
    age: Optional[int] = None
    dob: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=12, max_length=128)

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    roles: List[str]
    permissions: List[str]
    status: str
    mfa_enabled: bool
    force_password_change: bool
    phone: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionAssign(BaseModel):
    permission_ids: List[uuid.UUID]

class SecurityEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True

class APIKeyCreateResponse(BaseModel):
    api_key: APIKeyResponse
    raw_key: str
