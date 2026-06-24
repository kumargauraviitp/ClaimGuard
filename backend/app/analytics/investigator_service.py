from sqlalchemy import func, case, desc
from app.models import Investigation, InvestigationReport
from app.database import get_db

class InvestigatorService:
    def __init__(self, db):
        self.db = db

    def get_investigator_performance(self):
        stats = self.db.query(
            Investigation.investigator_id.label('investigator_id'),
            func.count(Investigation.id).label('total_cases'),
            func.sum(case((Investigation.status == 'Closed', 1), else_=0)).label('completed_cases'),
            func.sum(case((Investigation.status != 'Closed', 1), else_=0)).label('pending_cases'),
            func.avg(
                case((Investigation.status == 'Closed', 
                    func.extract('epoch', Investigation.updated_at) - func.extract('epoch', Investigation.created_at)),
                else_=0)
            ).label('avg_time_seconds')
        ).filter(Investigation.investigator_id != None)\
         .group_by(Investigation.investigator_id)\
         .order_by(desc('completed_cases'))\
         .all()
         
        results = []
        for s in stats:
            avg_days = round(s.avg_time_seconds / 86400, 1) if s.avg_time_seconds else 0.0
            
            # Subquery to calculate fraud confirmation rate for this specific investigator
            fraud_confirmed = self.db.query(func.count(InvestigationReport.id)).join(
                Investigation, Investigation.claim_id == InvestigationReport.claim_id
            ).filter(
                Investigation.investigator_id == s.investigator_id,
                InvestigationReport.approval_status == 'Approved'
            ).scalar() or 0
            
            confirm_rate = round((fraud_confirmed / s.completed_cases * 100), 1) if s.completed_cases > 0 else 0
            
            results.append({
                "investigator_id": s.investigator_id,
                "total_cases": s.total_cases,
                "completed_cases": s.completed_cases,
                "pending_cases": s.pending_cases,
                "average_resolution_time_days": avg_days,
                "fraud_confirmation_rate": confirm_rate
            })
            
        return results
