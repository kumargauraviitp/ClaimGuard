"""
Admin router for fraud rule management.

Endpoints:
- GET  /api/fraud-rules/policies       — list all known valid policies
- GET  /api/fraud-rules/vehicles       — list all known valid vehicles
- POST /api/fraud-rules/sync           — reload .txt files into DB
- GET  /api/fraud-rules/policies/file  — view raw policy.txt contents
- GET  /api/fraud-rules/vehicles/file  — view raw vehicle.txt contents
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.fraud_rules.reference_lists import (
    get_all_known_policies, get_all_known_vehicles,
    load_policy_file, load_vehicle_file, sync_lists_to_db,
)

router = APIRouter()


@router.get("/policies")
def list_known_policies(db: Session = Depends(get_db)):
    """List all policy numbers in the validation whitelist."""
    return {"policies": get_all_known_policies(db)}


@router.get("/vehicles")
def list_known_vehicles(db: Session = Depends(get_db)):
    """List all vehicle registration plates in the validation whitelist."""
    return {"vehicles": get_all_known_vehicles(db)}


@router.post("/sync")
def sync_reference_lists(db: Session = Depends(get_db)):
    """Reload the .txt files into the database tables."""
    p_count, v_count = sync_lists_to_db(db)
    return {
        "message": "Reference lists synced successfully",
        "policies_added": p_count,
        "vehicles_added": v_count,
    }


@router.get("/policies/file")
def view_policy_file():
    """View the raw policy.txt file contents."""
    return {"entries": load_policy_file()}


@router.get("/vehicles/file")
def view_vehicle_file():
    """View the raw vehicle.txt file contents."""
    return {"entries": load_vehicle_file()}
