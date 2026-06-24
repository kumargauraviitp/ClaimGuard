from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
import psutil
import os
import redis
from app.system.performance_service import performance_service
from app.config_manager import get_git_sha

router = APIRouter(prefix="/api/system", tags=["System Monitoring"])

@router.get("/health/live")
def health_live():
    return {"status": "alive"}

@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    # Check Postgres
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database is not ready")
        
    # Check Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.Redis.from_url(redis_url)
        r.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Redis is not ready")
        
    return {"status": "ready", "database": "connected", "redis": "connected"}

@router.get("/health/startup")
def health_startup():
    # Mocking check for model and KB logic
    # In a real scenario, we'd check if the global variables for the model are loaded
    from app.config_manager import CONFIG_LOCK_PATH
    import json
    
    status = {
        "status": "startup_complete",
        "config_loaded": os.path.exists(CONFIG_LOCK_PATH),
        "model_loaded": True, # Placeholder
        "knowledge_base_loaded": True, # Placeholder
        "shap_loaded": True # Placeholder
    }
    return status

@router.get("/metrics")
def system_metrics():
    # In a real scenario, total predictions and cache hit rates would be retrieved from DB/Redis
    return {
        "Total Predictions": 1024, # Mock
        "Average Prediction Time (ms)": performance_service.get_average("prediction"),
        "Average SHAP Time (ms)": performance_service.get_average("shap"),
        "Average KB Retrieval Time (ms)": performance_service.get_average("kb"),
        "Average RAG Generation Time (ms)": performance_service.get_average("rag"),
        "Average Agent Time (ms)": performance_service.get_average("agent"),
        "Cache Hit Rate": "85%"
    }

@router.get("/version")
def system_version():
    return {
        "Backend Version": "1.0.0",
        "Frontend Version": "1.0.0",
        "Model Version": "v2.1",
        "Knowledge Version": "v1.4",
        "Git SHA": get_git_sha(),
        "Build Time": "2026-06-21T00:00:00Z"
    }
