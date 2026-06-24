from sqlalchemy.orm import Session
from app.models import RefreshToken, User
from app.auth.jwt_service import JWTService
from datetime import datetime

class SessionService:
    @staticmethod
    def register_refresh_token(db: Session, user: User, token_str: str, expires_at: datetime) -> None:
        token = RefreshToken(user_id=user.id, token=token_str, expires_at=expires_at)
        db.add(token)
        db.commit()

    @staticmethod
    def revoke_refresh_token(db: Session, token_str: str) -> None:
        token = db.query(RefreshToken).filter(RefreshToken.token == token_str).first()
        if token:
            token.revoked = True
            db.commit()

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: str) -> None:
        """
        Revokes all refresh tokens for a user.
        Also we should ideally blacklist all their access tokens by emitting an event or tracking them,
        but typically revoking refresh tokens forces them to log out when the short-lived access token expires.
        """
        tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False).all()
        for t in tokens:
            t.revoked = True
        db.commit()

    @staticmethod
    def validate_refresh_token(db: Session, token_str: str) -> bool:
        token = db.query(RefreshToken).filter(RefreshToken.token == token_str).first()
        if not token:
            return False
        if token.revoked:
            return False
        if token.expires_at < datetime.utcnow():
            return False
        return True
