from sqlalchemy.orm import Session
from app.analytics.sql_metrics import SQLMetricsService
from app.analytics.drift_service import DriftService, ModelMonitorService
from app.analytics.agent_monitor import AgentMonitorService
from app.analytics.investigator_service import InvestigatorService

class AnalyticsService:
    def __init__(self, db: Session):
        self.sql_metrics = SQLMetricsService(db)
        self.drift_service = DriftService(db)
        self.model_monitor = ModelMonitorService(db)
        self.agent_monitor = AgentMonitorService(db)
        self.investigator_service = InvestigatorService(db)

    def generate_dashboard_json(self):
        executive_kpis = self.sql_metrics.get_executive_kpis()
        funnel = self.sql_metrics.get_investigation_funnel()
        geographic = self.sql_metrics.get_geographic_analytics()
        fraud_dist = self.sql_metrics.get_fraud_distribution_by_type()
        
        drift = self.drift_service.get_prediction_drift()
        model_stats = self.model_monitor.get_model_monitoring()
        agent_metrics = self.agent_monitor.get_agent_metrics()
        
        investigators = self.investigator_service.get_investigator_performance()
        
        return {
            "overview": executive_kpis,
            "investigation_funnel": funnel,
            "geographic_analytics": geographic,
            "fraud_by_type": fraud_dist,
            "prediction_drift": drift,
            "model_monitoring": model_stats,
            "agent_monitoring": agent_metrics,
            "investigator_performance": investigators,
            "generated_at": model_stats.get("training_date", "")  # Or simply timestamp
        }
