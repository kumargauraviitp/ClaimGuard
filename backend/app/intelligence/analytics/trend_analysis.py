from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import PredictionEvaluation
from datetime import datetime, timedelta
from typing import Dict, Any, List

class TrendAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def get_fraud_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze fraud trends over the specified time period."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Group by day and count total evaluations and total fraud cases
        daily_stats = self.db.query(
            func.date(PredictionEvaluation.reviewed_at).label('date'),
            func.count(PredictionEvaluation.id).label('total_cases'),
            func.sum(PredictionEvaluation.ground_truth).label('fraud_cases')
        ).filter(
            PredictionEvaluation.reviewed_at >= since_date
        ).group_by(
            func.date(PredictionEvaluation.reviewed_at)
        ).order_by(
            func.date(PredictionEvaluation.reviewed_at)
        ).all()
        
        trends = []
        for stat in daily_stats:
            fraud_rate = (stat.fraud_cases / stat.total_cases) if stat.total_cases > 0 else 0
            trends.append({
                "date": str(stat.date),
                "total_cases_reviewed": stat.total_cases,
                "confirmed_fraud_cases": int(stat.fraud_cases) if stat.fraud_cases else 0,
                "fraud_rate": float(fraud_rate)
            })
            
        return {
            "status": "completed",
            "period_days": days,
            "trends": trends
        }
