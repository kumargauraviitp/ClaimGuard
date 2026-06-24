"""
Reference lists for policy and vehicle verification.

Checks BOTH:
1. The .txt files (policy.txt, vehicle.txt) for manual reference
2. The PostgreSQL tables (known_policies, known_vehicles) for DB-level checks

Any claim whose policy number or registration is NOT found gets flagged as fraud risk.

The .txt files are what the user sees and edits.
The DB tables are what the rule engine queries at runtime.
They should stay in sync — use the sync_lists_to_db() function to reload .txt files into DB.
"""
import os
from typing import List, Tuple

from sqlalchemy.orm import Session

_DIR = os.path.dirname(os.path.abspath(__file__))
_POLICY_FILE = os.path.join(_DIR, "policy.txt")
_VEHICLE_FILE = os.path.join(_DIR, "vehicle.txt")


# ---------- .txt file helpers (for user reference) ----------

def load_policy_file() -> List[str]:
    """Load policy.txt entries as a list of raw strings."""
    if not os.path.exists(_POLICY_FILE):
        return []
    with open(_POLICY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_vehicle_file() -> List[str]:
    """Load vehicle.txt entries as a list of raw strings."""
    if not os.path.exists(_VEHICLE_FILE):
        return []
    with open(_VEHICLE_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# ---------- DB helpers (for rule engine queries) ----------

def is_valid_policy(db: Session, policy_number: str) -> bool:
    """Check if the policy number exists in the known_policies DB table."""
    if not policy_number:
        return False
    from app.models import KnownPolicy
    return db.query(KnownPolicy).filter(
        KnownPolicy.policy_number.ilike(policy_number.strip())
    ).first() is not None


def is_valid_vehicle(db: Session, license_plate: str) -> bool:
    """Check if the registration plate exists in the known_vehicles DB table."""
    if not license_plate:
        return False
    from app.models import KnownVehicle
    return db.query(KnownVehicle).filter(
        KnownVehicle.license_plate.ilike(license_plate.strip())
    ).first() is not None


def get_all_known_policies(db: Session) -> List[str]:
    """Get all known policy numbers from the DB."""
    from app.models import KnownPolicy
    rows = db.query(KnownPolicy.policy_number).all()
    return [r[0] for r in rows]


def get_all_known_vehicles(db: Session) -> List[str]:
    """Get all known registration plates from the DB."""
    from app.models import KnownVehicle
    rows = db.query(KnownVehicle.license_plate).all()
    return [r[0] for r in rows]


def sync_lists_to_db(db: Session) -> Tuple[int, int]:
    """
    Sync .txt file contents into the DB tables.
    Returns (policies_synced, vehicles_synced).
    Call this to add new entries after editing the .txt files.
    """
    from app.models import KnownPolicy, KnownVehicle

    policies = load_policy_file()
    vehicles = load_vehicle_file()

    p_count = 0
    for pn in policies:
        existing = db.query(KnownPolicy).filter(
            KnownPolicy.policy_number == pn.strip()
        ).first()
        if not existing:
            db.add(KnownPolicy(policy_number=pn.strip()))
            p_count += 1

    v_count = 0
    for lp in vehicles:
        existing = db.query(KnownVehicle).filter(
            KnownVehicle.license_plate == lp.strip()
        ).first()
        if not existing:
            db.add(KnownVehicle(license_plate=lp.strip()))
            v_count += 1

    db.commit()
    return (p_count, v_count)
