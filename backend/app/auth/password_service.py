from sqlalchemy.orm import Session
from app.models import User, PasswordHistory
from typing import List
import re
import bcrypt

class PasswordService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def get_password_hash(password: str) -> str:
        # bcrypt limits passwords to 72 bytes
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8')[:72], salt)
        return hashed.decode('utf-8')

    @staticmethod
    def validate_password_policy(password: str) -> None:
        """
        Enterprise Password Policy:
        - Minimum 12 characters
        - Maximum 128 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 number
        - At least 1 special character
        """
        if len(password) < 12 or len(password) > 128:
            raise ValueError("Password must be between 12 and 128 characters.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character.")

    @staticmethod
    def check_password_history(db: Session, user: User, new_password: str) -> None:
        """
        Ensures the new password hasn't been used in the last 5 passwords.
        """
        history = db.query(PasswordHistory).filter(PasswordHistory.user_id == user.id).order_by(PasswordHistory.changed_at.desc()).limit(5).all()
        for record in history:
            if PasswordService.verify_password(new_password, record.password_hash):
                raise ValueError("Password cannot be one of the last 5 used passwords.")

    @staticmethod
    def add_to_history(db: Session, user_id: str, password_hash: str) -> None:
        history_entry = PasswordHistory(user_id=user_id, password_hash=password_hash)
        db.add(history_entry)
        
        # Keep only the last 5
        all_history = db.query(PasswordHistory).filter(PasswordHistory.user_id == user_id).order_by(PasswordHistory.changed_at.desc()).all()
        if len(all_history) > 5:
            for entry in all_history[5:]:
                db.delete(entry)
        db.commit()
