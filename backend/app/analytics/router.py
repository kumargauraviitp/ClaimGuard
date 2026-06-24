from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.analytics.analytics_service import AnalyticsService
from app.analytics.audit_logger import AnalyticsAuditLogger, AnalyticsExportService
from app.models import DashboardCache
from typing import Optional
from datetime import datetime
from fastapi.responses import Response

router = APIRouter()

def get_cached_dashboard(db: Session, start_date: Optional[datetime], end_date: Optional[datetime], role: str):
    # Only return cache if we are querying the default global state (Admin, no dates)
    if role == "Admin" and not start_date and not end_date:
        cache = db.query(DashboardCache).filter(DashboardCache.dashboard_key == "main").first()
        if cache and cache.expires_at > datetime.utcnow():
            return cache.dashboard_json
    return None

from app.auth.permission_service import get_current_user_or_api_key

@router.get("/overview")
def get_overview(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    current_user = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_role = roles[0] if roles else "Investigator"
    
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        from app.models import Claim
        customer_claims = db.query(Claim).filter(Claim.customer_id == current_user.customer_id).all()
        return {
            "total_claims": len(customer_claims),
            "fraud_claims": len([c for c in customer_claims if c.workflow_status in ['investigation_started', 'fraud_detected', 'rejected']]),
            "fraud_rate": 0,
            "pending_investigations": len([c for c in customer_claims if c.workflow_status in ['pending_review', 'investigation_started']]),
            "completed_investigations": len([c for c in customer_claims if c.workflow_status in ['approved', 'rejected']]),
            "avg_investigation_time_days": 0
        }

    cached = get_cached_dashboard(db, start_date, end_date, user_role)
    if cached and "overview" in cached:
        return cached["overview"]
    return AnalyticsService(db).sql_metrics.get_executive_kpis(start_date, end_date, user_role)

@router.get("/claims")
def get_claims_analytics(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    current_user = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_role = roles[0] if roles else "Investigator"
    
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        return []

    cached = get_cached_dashboard(db, start_date, end_date, user_role)
    if cached and "fraud_by_type" in cached:
        return cached["fraud_by_type"]
    return AnalyticsService(db).sql_metrics.get_fraud_distribution_by_type(start_date, end_date, user_role)


@router.get("/trend")
def get_fraud_trend(
    interval: str = "monthly",
    current_user = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_role = roles[0] if roles else "Investigator"
    
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        return []
        
    return AnalyticsService(db).sql_metrics.get_fraud_trend(interval=interval, role=user_role)


@router.get("/distribution")
def get_fraud_distribution_chart(
    current_user = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_role = roles[0] if roles else "Investigator"
    
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        from app.models import Claim
        customer_claims = db.query(Claim).filter(Claim.customer_id == current_user.customer_id).all()
        approved = len([c for c in customer_claims if c.workflow_status == 'approved'])
        rejected = len([c for c in customer_claims if c.workflow_status == 'rejected'])
        pending = len([c for c in customer_claims if c.workflow_status not in ['approved', 'rejected']])
        return [
            {"name": "Approved", "value": approved},
            {"name": "Rejected", "value": rejected},
            {"name": "Pending", "value": pending}
        ]
        
    return AnalyticsService(db).sql_metrics.get_fraud_distribution_chart(role=user_role)

@router.get("/fraud")
def get_fraud_analytics(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    current_user = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_role = roles[0] if roles else "Investigator"
    
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        return []
        
    cached = get_cached_dashboard(db, start_date, end_date, user_role)
    if cached and "geographic_analytics" in cached:
        return cached["geographic_analytics"]
    return AnalyticsService(db).sql_metrics.get_geographic_analytics(start_date, end_date, user_role)

@router.get("/investigations")
def get_investigations_funnel(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    current_user = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    roles = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_role = roles[0] if roles else "Investigator"
    
    if "Customer" in roles and "Admin" not in roles and "Investigator" not in roles:
        return []
        
    cached = get_cached_dashboard(db, start_date, end_date, user_role)
    if cached and "investigation_funnel" in cached:
        return cached["investigation_funnel"]
    return AnalyticsService(db).sql_metrics.get_investigation_funnel(start_date, end_date, user_role)

@router.get("/models")
def get_model_monitoring(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    x_user_role: Optional[str] = Header("Admin"),
    db: Session = Depends(get_db)
):
    if x_user_role == "Investigator":
        return {"drift": {}, "monitoring": {}}

    cached = get_cached_dashboard(db, start_date, end_date, x_user_role)
    if cached and "model_monitoring" in cached:
        return {
            "drift": cached.get("prediction_drift"),
            "monitoring": cached["model_monitoring"]
        }
    service = AnalyticsService(db)
    # Note: drift/model metrics don't take date filters directly right now as they compare global windows
    return {
        "drift": service.drift_service.get_prediction_drift(),
        "monitoring": service.model_monitor.get_model_monitoring()
    }

@router.get("/agents")
def get_agent_monitoring(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    x_user_role: Optional[str] = Header("Admin"),
    db: Session = Depends(get_db)
):
    if x_user_role == "Investigator":
        return {"total_executions": 0, "average_latency_ms": 0, "average_cost_usd": 0, "success_rate": 0}

    cached = get_cached_dashboard(db, start_date, end_date, x_user_role)
    if cached and "agent_monitoring" in cached:
        return cached["agent_monitoring"]
    return AnalyticsService(db).agent_monitor.get_agent_metrics()

@router.get("/investigators")
def get_investigator_performance(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    x_user_role: Optional[str] = Header("Admin"),
    db: Session = Depends(get_db)
):
    cached = get_cached_dashboard(db, start_date, end_date, x_user_role)
    if cached and "investigator_performance" in cached:
        return cached["investigator_performance"]
    # Pass user_role if needed, investigator_service just grabs all anyway
    return AnalyticsService(db).investigator_service.get_investigator_performance()

@router.get("/export")
def export_dashboard(format: str = "csv", x_user_role: str = Header("Admin"), db: Session = Depends(get_db)):
    logger = AnalyticsAuditLogger(db)
    logger.log_export(user_id="user_placeholder", dashboard_viewed="full_export", export_format=format)
    
    if x_user_role == "Investigator":
        raise HTTPException(status_code=403, detail="Investigators cannot export global dashboards.")

    cached = get_cached_dashboard(db, None, None, x_user_role)
    if not cached:
        cached = AnalyticsService(db).generate_dashboard_json()
        
    if format == "csv":
        csv_data = AnalyticsExportService.export_csv(cached, "investigator_performance")
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=investigators.csv"})
    elif format == "json":
        return cached
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format.")
