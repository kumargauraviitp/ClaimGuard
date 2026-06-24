from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import RevokedToken, User
from app.auth.secrets_manager import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import uuid

class JWTService:
    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = str(uuid.uuid4())
        to_encode.update({"exp": expire, "jti": jti, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())
        to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, db: Session, expected_type: str = "access") -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check if token type matches
            if payload.get("type") != expected_type:
                return None
                
            # Check JTI Blacklist (Revoked Tokens)
            jti = payload.get("jti")
            if jti:
                is_revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
                if is_revoked:
                    return None
            return payload
        except JWTError:
            return None

    @staticmethod
    def revoke_token(db: Session, token: str) -> None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            jti = payload.get("jti")
            if jti:
                # Add to RevokedTokens table
                existing = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
                if not existing:
                    db.add(RevokedToken(jti=jti))
                    db.commit()
        except JWTError:
            pass
