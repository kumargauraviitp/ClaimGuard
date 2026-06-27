import secrets
import string
import logging
from sqlalchemy.orm import Session
from app.models import User, Role, Permission
from app.auth.password_service import PasswordService
from app.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_random_password(length=24):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+"
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*()_+" for c in password)):
            return password

def seed_admin():
    db: Session = SessionLocal()
    try:
        # Check if admin role exists
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            admin_role = Role(name="Admin", description="System Administrator")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        # Check if superuser permission exists
        super_perm = db.query(Permission).filter(Permission.name == "*").first()
        if not super_perm:
            super_perm = Permission(name="*", description="All permissions")
            db.add(super_perm)
            db.commit()
            db.refresh(super_perm)
            
            admin_role.permissions.append(super_perm)
            db.commit()

        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            password = "admin123"
            password_hash = PasswordService.get_password_hash(password)
            
            admin_user = User(
                username="admin",
                full_name="System Administrator",
                email="admin@insurance-platform.local",
                password_hash=password_hash,
                force_password_change=True,
                status="Active"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            admin_user.roles.append(admin_role)
            db.commit()
            
            logger.info("="*50)
            logger.info("DEFAULT ADMIN USER CREATED")
            logger.info("Username: admin")
            logger.info("Password: admin123")
            logger.info("YOU MUST CHANGE THIS PASSWORD ON FIRST LOGIN.")
            logger.info("="*50)
        else:
            logger.info("Admin user already exists. Skipping seed.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
