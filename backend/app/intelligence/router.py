from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from uuid import UUID

from app.database import get_db
from app.auth.router import get_current_user_or_api_key
from app.models import User
from app.intelligence.drift.concept_drift import ConceptDriftMonitor
from app.intelligence.analytics.fraud_network import FraudNetworkAnalyzer
from app.intelligence.analytics.trend_analysis import TrendAnalyzer
from app.intelligence.recommendation.decision_support import DecisionSupportEngine

router = APIRouter(prefix="/api/intelligence", tags=["Fraud Intelligence"])

@router.get("/drift/concept")
def check_concept_drift(
    window_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key)
):
    """Check for concept drift in fraud models."""
    monitor = ConceptDriftMonitor(db)
    return monitor.check_concept_drift(window_days)

@router.get("/analytics/network/{claim_id}")
def analyze_fraud_network(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key)
):
    """Find linked fraud cases to detect fraud rings."""
    analyzer = FraudNetworkAnalyzer(db)
    return analyzer.find_linked_fraud_cases(claim_id)

@router.get("/analytics/trends")
def get_fraud_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key)
):
    """Analyze fraud trends over time."""
    analyzer = TrendAnalyzer(db)
    return analyzer.get_fraud_trends(days)

@router.get("/recommendations/{prediction_id}")
def get_decision_support(
    prediction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key)
):
    """Generate recommendations for a specific prediction."""
    engine = DecisionSupportEngine(db)
    return engine.generate_recommendations(prediction_id)
