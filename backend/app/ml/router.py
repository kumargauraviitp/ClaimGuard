from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from .preprocessing import DataPreprocessor

router = APIRouter(prefix="/api/preprocessing", tags=["preprocessing"])

@router.post("/run", response_model=schemas.PreprocessingRunResponse)
def run_preprocessing(payload: schemas.PreprocessingRunRequest, db: Session = Depends(get_db)):
    preprocessor = DataPreprocessor(db)
    
    feature_vector, metrics = preprocessor.process_claim(str(payload.claim_id))
    
    if metrics["status"] == "failed":
        # We don't raise 500 because we want to return the error log payload to the client
        pass

    return schemas.PreprocessingRunResponse(
        claim_id=payload.claim_id,
        status=metrics["status"],
        feature_vector=feature_vector if feature_vector else None,
        processing_time_ms=metrics["processing_time_ms"],
        missing_values_imputed=metrics["missing_values_imputed"],
        features_engineered=metrics["features_engineered"],
        warnings=metrics["warnings"],
        errors=metrics["errors"]
    )

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    # Check if artifacts exist
    import os
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts")
    scaler_exists = os.path.exists(os.path.join(artifacts_dir, "scaler.pkl"))
    encoder_exists = os.path.exists(os.path.join(artifacts_dir, "encoder.pkl"))
    features_exists = os.path.exists(os.path.join(artifacts_dir, "features.json"))
    
    pipeline_ready = scaler_exists and encoder_exists and features_exists
    
    return {
        "status": "ready" if pipeline_ready else "not_ready",
        "artifacts": {
            "scaler": scaler_exists,
            "encoder": encoder_exists,
            "features": features_exists
        }
    }

@router.get("/logs/{claim_id}", response_model=List[schemas.PreprocessingLogResponse])
def get_logs(claim_id: str, db: Session = Depends(get_db)):
    logs = db.query(models.PreprocessingLog).filter(models.PreprocessingLog.claim_id == claim_id).order_by(models.PreprocessingLog.created_at.desc()).all()
    if not logs:
        raise HTTPException(status_code=404, detail="No preprocessing logs found for this claim.")
    return logs

@router.post("/validate", response_model=schemas.PreprocessingValidationResponse)
def validate_raw_claim(payload: schemas.ClaimSubmissionWizard):
    # Basic pre-flight validation before DB insertion
    errors = []
    warnings = []
    
    if payload.claimAmount and payload.claimAmount < 0:
        errors.append("Claim amount cannot be negative.")
        
    if payload.incidentDate:
        from datetime import datetime
        try:
            inc_date = datetime.strptime(payload.incidentDate, "%Y-%m-%d").date()
            if inc_date > datetime.utcnow().date():
                errors.append("Incident date cannot be in the future.")
        except ValueError:
            errors.append("Invalid date format.")
            
    if payload.hasPoliceReport == "yes" and not payload.police_report_number:
        errors.append("Police report number is mandatory if police report is filed.")
        
    return schemas.PreprocessingValidationResponse(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
from .serving import FraudModelService

@router.post("/claims/{claim_id}/predict", response_model=schemas.PredictionResponse)
def predict_fraud(claim_id: str, db: Session = Depends(get_db)):
    service = FraudModelService()
    prediction = service.predict(claim_id, db)
    if not prediction:
        raise HTTPException(status_code=500, detail="Prediction failed or model not ready.")
    return prediction

@router.post("/claims/batch-predict")
def batch_predict(claim_ids: List[str], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    def run_batch_prediction(c_ids: List[str]):
        from app.database import SessionLocal
        bg_db = SessionLocal()
        try:
            service = FraudModelService()
            for c_id in c_ids:
                service.predict(c_id, bg_db)
        finally:
            bg_db.close()
            
    background_tasks.add_task(run_batch_prediction, claim_ids)
    return {"status": "Batch prediction started in background for {} claims".format(len(claim_ids))}

@router.get("/ml/health")
def model_health(db: Session = Depends(get_db)):
    service = FraudModelService()
    return service.get_health_stats(db)
