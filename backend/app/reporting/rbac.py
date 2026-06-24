from fastapi import HTTPException, status, Depends
from typing import List

# Mock user object for RBAC (in real world, this would come from JWT or Session)
class UserContext:
    def __init__(self, user_id: str, role: str, permissions: List[str]):
        self.user_id = user_id
        self.role = role
        self.permissions = permissions

def get_current_user() -> UserContext:
    # Dummy mock - default to an admin investigator
    return UserContext(user_id="user_admin_123", role="manager", permissions=["read", "write", "approve", "export"])

def require_role(allowed_roles: List[str]):
    def role_checker(user: UserContext = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' is not permitted. Allowed roles: {allowed_roles}"
            )
        return user
    return role_checker

def require_permission(permission: str):
    def permission_checker(user: UserContext = Depends(get_current_user)):
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )
        return user
    return permission_checker
