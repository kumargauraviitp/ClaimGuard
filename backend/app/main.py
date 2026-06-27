from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timedelta, date
from typing import List
import uuid

from .database import get_db, Base, engine
from . import models, schemas
from .ml import router as ml_router
from .ml import training_router

from app.explainability.router import router as explain_router
from app.knowledge.router import router as knowledge_router
from app.rag.router import router as rag_router
from app.agent.router import router as agent_router
from app.agent.multi_agent_router import router as multi_agent_router
from app.reporting.router import router as reporting_router
from app.feedback.router import router as feedback_router
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.logging.correlation import set_correlation_id
from app.system.router import router as system_router

# Create the database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    from app.analytics.scheduler import scheduler
    from app.database import engine
    from app.auth.seed_admin import seed_admin
    
    # Ensure default admin user exists
    seed_admin()
    
    scheduler.start()
    yield
    # Shutdown logic
    scheduler.stop()
    engine.dispose()

app = FastAPI(
    title="Insurance Fraud AI Platform",
    description="API for the AI-Powered Insurance Claim Fraud Detection & Investigation Platform",
    version="1.0.0",
    lifespan=lifespan
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Don't add security headers to CORS preflight requests
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        corr_id = request.headers.get("X-Correlation-ID")
        set_correlation_id(corr_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = set_correlation_id()
        return response

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

from app.auth.router import router as auth_router
app.include_router(auth_router)

from app.auth.permission_service import get_current_user_or_api_key

app.include_router(ml_router.router, dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(training_router.router, dependencies=[Depends(get_current_user_or_api_key)])

app.include_router(explain_router, prefix="/api", dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(knowledge_router, prefix="/api", dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(rag_router, prefix="/api", dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(agent_router, prefix="/api", dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(multi_agent_router, prefix="/api", dependencies=[Depends(get_current_user_or_api_key)])
from app.intelligence.router import router as intelligence_router

app.include_router(reporting_router, dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(system_router)
from app.backup.router import router as backup_router
app.include_router(backup_router, dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(feedback_router, dependencies=[Depends(get_current_user_or_api_key)])
app.include_router(intelligence_router, dependencies=[Depends(get_current_user_or_api_key)])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "http://localhost:80", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Insurance Fraud AI API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        
    return {
        "status": "ok",
        "database": db_status
    }

# --- Claims API ---
@app.post("/api/claims", response_model=schemas.ClaimResponse)
@limiter.limit("5/minute")
def create_or_save_claim(
    request: Request,
    payload: schemas.ClaimSubmissionWizard, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_api_key)
):
    # 1. Create or Find Customer
    customer = None
    if payload.email:
        customer = db.query(models.Customer).filter(models.Customer.email == payload.email).first()
    
    if not customer and payload.email:
        first_name = payload.name.split(" ")[0] if payload.name else "Unknown"
        last_name = " ".join(payload.name.split(" ")[1:]) if payload.name and " " in payload.name else ""
        customer = models.Customer(
            first_name=first_name,
            last_name=last_name,
            email=payload.email,
            phone=payload.phone,
            city=payload.city,
            age=payload.age,
            gender=payload.gender,
            occupation=payload.occupation
        )
        db.add(customer)
        db.flush()

    if not customer:
        # Require customer email to proceed, even for drafts
        raise HTTPException(status_code=400, detail="Customer email is required")

    # 2. Create Vehicle (or reuse existing one with same license plate)
    plate = payload.regNumber or "UNKNOWN"
    vehicle = None
    if plate and plate != "UNKNOWN":
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.license_plate == plate).first()
    if not vehicle:
        vehicle = models.Vehicle(
            vin=f"VIN{uuid.uuid4().hex[:14].upper()}", # Dummy VIN for testing
            make=payload.make or "Unknown",
            model=payload.model or "Unknown",
            year=payload.year or 2020,
            license_plate=plate,
            color=payload.color,
            vehicle_type=payload.vehicle_type,
            fuel_type=payload.fuel_type,
            purchase_price=payload.purchase_price,
            current_market_value=payload.current_market_value
        )
        db.add(vehicle)
        db.flush()

    # 3. Create Policy (or reuse existing one with same policy number)
    pol_num = payload.policyNumber or f"POL-{uuid.uuid4().hex[:8].upper()}"
    policy = None
    if payload.policyNumber:
        policy = db.query(models.Policy).filter(models.Policy.policy_number == pol_num).first()
    if not policy:
        policy = models.Policy(
            policy_number=pol_num,
            customer_id=customer.id,
            policy_type=payload.policyType or "unknown",
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow() + timedelta(days=365),
            premium=(payload.insuredValue or 0) * 0.05,
            deductible=(payload.insuredValue or 0) * 0.01,
            coverage_limit=payload.insuredValue or 0
        )
        db.add(policy)
        db.flush()

    # 4. Create Claim Core
    try:
        inc_date = datetime.strptime(payload.incidentDate, "%Y-%m-%d").date() if payload.incidentDate else date.today()
    except ValueError:
        inc_date = date.today()

    delay_days = max(0, (date.today() - inc_date).days)

    claim = models.Claim(
        claim_number=f"CLM-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}",
        policy_id=policy.id,
        customer_id=customer.id,
        vehicle_id=vehicle.id,
        filing_date=datetime.utcnow(),
        reporting_delay_days=delay_days,
        status=payload.status,
        workflow_status="pending_review" if payload.status == "submitted" else "drafting"
    )
    db.add(claim)
    db.flush()

    # 5. Create Accident
    accident = models.Accident(
        claim_id=claim.id,
        incident_date=inc_date,
        accident_location=payload.location,
        weather_condition=payload.weather_conditions,
        road_condition=payload.road_conditions,
        accident_description=payload.description,
        vehicle_speed=payload.vehicle_speed,
        number_of_vehicles_involved=payload.number_of_vehicles_involved,
        number_of_injured=payload.number_of_injured
    )
    db.add(accident)

    # 6. Create Financial Details
    financials = models.FinancialDetails(
        claim_id=claim.id,
        claim_amount=payload.claimAmount or 0.0,
        repair_estimate=payload.repair_estimate,
        medical_expenses=payload.medical_expenses,
        hospital_charges=payload.hospital_charges,
        towing_charges=payload.towing_charges,
        other_expenses=payload.additional_expenses
    )
    db.add(financials)

    # 7. Create Police Details
    police = models.PoliceDetails(
        claim_id=claim.id,
        police_report_available=payload.hasPoliceReport == "yes",
        fir_number=payload.police_report_number,
        police_station=payload.police_station
    )
    db.add(police)

    # 8. Create Witness
    if payload.witnesses == "yes" and payload.witness_name:
        witness = models.Witness(
            claim_id=claim.id,
            name=payload.witness_name,
            phone=payload.witness_contact,
            statement=payload.witness_details
        )
        db.add(witness)

    # 9. Log Activity
    action = "CLAIM_SUBMITTED" if payload.status == "submitted" else "DRAFT_SAVED"
    log = models.ActivityLog(
        claim_id=claim.id,
        action=action,
        user_id=str(customer.id)
    )
    db.add(log)

    db.commit()
    db.refresh(claim)
    
    if payload.status == "submitted":
        from app.ml.serving import FraudModelService
        def run_prediction_task(c_id: str):
            # Use a fresh db session for background task
            from app.database import SessionLocal
            bg_db = SessionLocal()
            try:
                service = FraudModelService()
                service.predict(c_id, bg_db)
            finally:
                bg_db.close()
                
        background_tasks.add_task(run_prediction_task, str(claim.id))
        
    return claim

@app.get("/api/claims", response_model=List[schemas.ClaimResponse])
def get_claims(db: Session = Depends(get_db), current_user = Depends(get_current_user_or_api_key)):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    query = db.query(models.Claim).options(
        joinedload(models.Claim.customer),
        joinedload(models.Claim.policy),
        joinedload(models.Claim.vehicle),
        joinedload(models.Claim.accident),
        joinedload(models.Claim.financial_details),
        joinedload(models.Claim.police_details),
        selectinload(models.Claim.witnesses),
        selectinload(models.Claim.predictions),
        selectinload(models.Claim.documents),
        selectinload(models.Claim.activity_logs),
        selectinload(models.Claim.feedback),
    )

    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        query = query.filter(models.Claim.customer_id == current_user.customer_id)

    return query.order_by(desc(models.Claim.created_at)).all()

@app.get("/api/claims/{claim_id}", response_model=schemas.ClaimResponse)
def get_claim(claim_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user_or_api_key)):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    claim = db.query(models.Claim).options(
        joinedload(models.Claim.customer),
        joinedload(models.Claim.policy),
        joinedload(models.Claim.vehicle),
        joinedload(models.Claim.accident),
        joinedload(models.Claim.financial_details),
        joinedload(models.Claim.police_details),
        selectinload(models.Claim.witnesses),
        selectinload(models.Claim.predictions),
        selectinload(models.Claim.documents),
        selectinload(models.Claim.activity_logs),
        selectinload(models.Claim.feedback),
    ).filter(models.Claim.id == claim_id).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        if str(claim.customer_id) != str(current_user.customer_id):
            raise HTTPException(status_code=403, detail="Not authorized to view this claim")
            
    return claim

@app.post("/api/claims/{claim_id}/scan", response_model=schemas.ClaimResponse)
def run_manual_scan(claim_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user_or_api_key)):
    claim = db.query(models.Claim).options(
        joinedload(models.Claim.customer),
        joinedload(models.Claim.policy),
        joinedload(models.Claim.vehicle),
        joinedload(models.Claim.accident),
        joinedload(models.Claim.financial_details),
        joinedload(models.Claim.police_details),
        selectinload(models.Claim.witnesses),
        selectinload(models.Claim.predictions),
        selectinload(models.Claim.documents),
        selectinload(models.Claim.activity_logs),
        selectinload(models.Claim.feedback),
    ).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    from app.ml.serving import FraudModelService
    service = FraudModelService()
    try:
        service.predict(claim_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Prediction failed: {str(e)}")
        
    # Refresh to get predictions and SHAP values
    db.refresh(claim)
    return claim

@app.delete("/api/claims/{claim_id}")
def delete_claim(claim_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user_or_api_key)):
    """Delete a claim. Admin-only — other roles get 403."""
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "Admin" not in roles:
        raise HTTPException(status_code=403, detail="Only admins can delete claims")

    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_number = claim.claim_number
    db.delete(claim)
    db.commit()
    return {"detail": f"Claim {claim_number} deleted successfully"}

from app.analytics.router import router as analytics_router

app.include_router(analytics_router, prefix="/api/analytics", dependencies=[Depends(get_current_user_or_api_key)])

from app.documents.router import router as documents_router

app.include_router(documents_router, prefix="/api", dependencies=[Depends(get_current_user_or_api_key)])

# Also expose known policies/vehicles endpoints for admin
from app.fraud_rules.admin_router import router as fraud_admin_router

app.include_router(fraud_admin_router, prefix="/api/fraud-rules", dependencies=[Depends(get_current_user_or_api_key)])
