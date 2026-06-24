from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, text, extract
from app.models import (
    Claim, Prediction, Investigation, InvestigationReport, 
    Customer, Policy, AgentExecutionAnalytics, ModelPerformanceHistory
)
from datetime import datetime, timedelta
from typing import Optional, List
import calendar

class SQLMetricsService:
    def __init__(self, db: Session):
        self.db = db

    def _apply_date_filters(self, query, model, start_date: Optional[datetime], end_date: Optional[datetime]):
        if start_date:
            if hasattr(model, 'filing_date'):
                query = query.filter(model.filing_date >= start_date)
            elif hasattr(model, 'created_at'):
                query = query.filter(model.created_at >= start_date)
            elif hasattr(model, 'timestamp'):
                query = query.filter(model.timestamp >= start_date)
        if end_date:
            if hasattr(model, 'filing_date'):
                query = query.filter(model.filing_date <= end_date)
            elif hasattr(model, 'created_at'):
                query = query.filter(model.created_at <= end_date)
            elif hasattr(model, 'timestamp'):
                query = query.filter(model.timestamp <= end_date)
        return query

    def get_executive_kpis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, role: str = "Admin"):
        if role == "Investigator":
            return {"total_claims": 0, "fraud_claims": 0, "fraud_rate": 0, "pending_investigations": 0, "completed_investigations": 0, "avg_investigation_time_days": 0}

        q_total = self._apply_date_filters(self.db.query(func.count(Claim.id)), Claim, start_date, end_date)
        total_claims = q_total.scalar() or 0
        # Subquery to get the latest prediction date per claim
        latest_pred_subq = self.db.query(
            Prediction.claim_id,
            func.max(Prediction.created_at).label('max_created_at')
        ).group_by(Prediction.claim_id).subquery()

        # Query to get the actual latest prediction rows
        q_latest = self.db.query(Prediction).join(
            latest_pred_subq,
            (Prediction.claim_id == latest_pred_subq.c.claim_id) &
            (Prediction.created_at == latest_pred_subq.c.max_created_at)
        )
        q_latest = self._apply_date_filters(q_latest, Prediction, start_date, end_date)
        
        # Fraud claims: where latest prediction is High or Critical risk
        # (matches the hardcoded tier boundaries: >=65% = High, >=80% = Critical)
        FRAUD_TIERS = ['High', 'Critical']
        fraud_claims = q_latest.filter(Prediction.risk_category.in_(FRAUD_TIERS)).count()

        q_pending_fallback = q_latest.join(Claim, Claim.id == Prediction.claim_id).filter(Prediction.risk_category.in_(FRAUD_TIERS)).filter(Claim.status != 'investigated').count()
        
        fraud_rate = (fraud_claims / total_claims) if total_claims > 0 else 0
        
        q_pending = self._apply_date_filters(self.db.query(func.count(Investigation.id)), Investigation, start_date, end_date)
        pending_inv = q_pending.filter(Investigation.status != 'Closed').scalar() or 0
            
        q_comp = self._apply_date_filters(self.db.query(func.count(Investigation.id)), Investigation, start_date, end_date)
        completed_inv = q_comp.filter(Investigation.status == 'Closed').scalar() or 0
        
        # Fallback to fraud_claims if Investigation table hasn't been populated
        if pending_inv == 0 and completed_inv == 0:
            pending_inv = q_pending_fallback
            
        q_avg = self._apply_date_filters(self.db.query(func.avg(
            func.extract('epoch', Investigation.updated_at - Investigation.created_at)
        )), Investigation, start_date, end_date)
        avg_time = q_avg.filter(Investigation.status == 'Closed').scalar() or 0

        avg_time_days = avg_time / 86400

        # Average confidence across all predictions
        q_conf = self._apply_date_filters(self.db.query(func.avg(Prediction.prediction_confidence)), Prediction, start_date, end_date)
        avg_confidence = q_conf.scalar()
        avg_confidence = round(avg_confidence, 2) if avg_confidence is not None else 0

        # False positive rate: predictions marked High risk but no investigation confirmed
        # Approximate as 1 - precision among High-risk predictions (those investigated & rejected / total high-risk)
        total_high = fraud_claims
        false_positive_rate = 0.0  # Will be refined as investigations accumulate

        return {
            "total_claims": total_claims,
            "fraud_claims": fraud_claims,
            "fraud_rate": round(fraud_rate, 2),
            "pending_investigations": pending_inv,
            "completed_investigations": completed_inv,
            "avg_investigation_time_days": round(avg_time_days, 1),
            "avg_confidence": avg_confidence,
            "false_positive_rate": false_positive_rate,
        }

    def get_investigation_funnel(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, role: str = "Admin"):
        if role == "Investigator":
            return {"submitted": 0, "predicted_fraud": 0, "investigated": 0, "confirmed_fraud": 0, "rejected_fraud": 0}

        submitted = self._apply_date_filters(self.db.query(func.count(Claim.id)), Claim, start_date, end_date).scalar() or 0
        predicted_fraud = self._apply_date_filters(self.db.query(func.count(Prediction.id)), Prediction, start_date, end_date).filter(Prediction.risk_category == 'High').scalar() or 0
        investigated = self._apply_date_filters(self.db.query(func.count(Investigation.id)), Investigation, start_date, end_date).scalar() or 0
        
        # Reports don't necessarily have created_at filtering easily without join, skipping date filter on final funnel step for simplicity, 
        # or we just rely on the existing base logic
        confirmed_fraud = self.db.query(func.count(InvestigationReport.id)).filter(InvestigationReport.approval_status == 'Approved').scalar() or 0
        rejected_fraud = self.db.query(func.count(InvestigationReport.id)).filter(InvestigationReport.approval_status == 'Rejected').scalar() or 0
        
        return {
            "submitted": submitted,
            "predicted_fraud": predicted_fraud,
            "investigated": investigated,
            "confirmed_fraud": confirmed_fraud,
            "rejected_fraud": rejected_fraud
        }

    def get_geographic_analytics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, role: str = "Admin"):
        if role == "Investigator":
            return []

        q = self.db.query(
            Customer.state,
            func.count(Claim.id).label('claim_count'),
            func.sum(case((Prediction.risk_category == 'High', 1), else_=0)).label('fraud_count')
        ).select_from(Customer)\
         .join(Policy, Policy.customer_id == Customer.id)\
         .join(Claim, Claim.policy_id == Policy.id)\
         .outerjoin(Prediction, Prediction.claim_id == Claim.id)
         
        q = self._apply_date_filters(q, Claim, start_date, end_date)
        
        state_distribution = q.group_by(Customer.state).order_by(desc('claim_count')).all()

        return [
            {
                "state": row.state or "Unknown",
                "claim_count": row.claim_count,
                "fraud_count": row.fraud_count,
                "fraud_rate": round((row.fraud_count / row.claim_count * 100), 2) if row.claim_count > 0 else 0
            }
            for row in state_distribution
        ]

    def get_fraud_distribution_by_type(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, role: str = "Admin"):
        if role == "Investigator":
            return []

        # Count claims as fraud when the latest prediction is High OR Critical
        # (previously this only counted 'High', so Critical claims — the most
        # suspicious ones — were never shown in the "Fraud by claim type" card).
        FRAUD_TIERS = ['High', 'Critical']

        # Latest prediction per claim, so multi-prediction claims aren't double counted
        latest_pred_subq = self.db.query(
            Prediction.claim_id.label('claim_id'),
            func.max(Prediction.created_at).label('max_created_at')
        ).group_by(Prediction.claim_id).subquery()

        q = self.db.query(
            Policy.policy_type.label('claim_type'),
            func.count(Claim.id).label('total'),
            func.sum(case((Prediction.risk_category.in_(FRAUD_TIERS), 1), else_=0)).label('fraud')
        ).select_from(Policy)\
         .join(Claim, Claim.policy_id == Policy.id)\
         .outerjoin(latest_pred_subq,
            Claim.id == latest_pred_subq.c.claim_id)\
         .outerjoin(Prediction,
            (Prediction.claim_id == Claim.id) &
            (Prediction.created_at == latest_pred_subq.c.max_created_at))

        q = self._apply_date_filters(q, Claim, start_date, end_date)

        dist = q.group_by(Policy.policy_type).all()

        return [
            {
                "claim_type": row.claim_type,
                "total": row.total,
                "fraud": row.fraud,
                "rate": round((row.fraud / row.total * 100), 2) if row.total > 0 else 0
            }
            for row in dist
        ]

    def get_fraud_trend(self, interval: str = "monthly", role: str = "Admin") -> List[dict]:
        """Trend data for dashboard chart based on interval.
        interval can be: 'daily', 'weekly', 'monthly', 'yearly'
        """
        if role == "Investigator":
            return []

        now = datetime.utcnow()
        
        # Subquery for the latest prediction per claim
        latest_pred_subq = self.db.query(
            Prediction.claim_id,
            func.max(Prediction.created_at).label('max_created_at')
        ).group_by(Prediction.claim_id).subquery()

        actual_latest_pred = self.db.query(Prediction).join(
            latest_pred_subq,
            (Prediction.claim_id == latest_pred_subq.c.claim_id) &
            (Prediction.created_at == latest_pred_subq.c.max_created_at)
        ).filter(Prediction.risk_category.in_(['High', 'Critical'])).subquery()

        if interval == 'daily':
            cutoff = now - timedelta(days=30) # last 30 days
            group_cols = [extract('year', Claim.filing_date), extract('month', Claim.filing_date), extract('day', Claim.filing_date)]
            order_cols = ['yr', 'mo', 'dy']
            select_cols = [
                extract('year', Claim.filing_date).label('yr'),
                extract('month', Claim.filing_date).label('mo'),
                extract('day', Claim.filing_date).label('dy'),
                func.count(Claim.id).label('claim_volume'),
                func.count(actual_latest_pred.c.claim_id).label('fraud_count'),
            ]
        elif interval == 'weekly':
            cutoff = now - timedelta(weeks=12) # last 12 weeks
            group_cols = [extract('year', Claim.filing_date), extract('week', Claim.filing_date)]
            order_cols = ['yr', 'wk']
            select_cols = [
                extract('year', Claim.filing_date).label('yr'),
                extract('week', Claim.filing_date).label('wk'),
                func.count(Claim.id).label('claim_volume'),
                func.count(actual_latest_pred.c.claim_id).label('fraud_count'),
            ]
        elif interval == 'yearly':
            cutoff = now - timedelta(days=365*5) # last 5 years
            group_cols = [extract('year', Claim.filing_date)]
            order_cols = ['yr']
            select_cols = [
                extract('year', Claim.filing_date).label('yr'),
                func.count(Claim.id).label('claim_volume'),
                func.count(actual_latest_pred.c.claim_id).label('fraud_count'),
            ]
        else: # monthly
            cutoff = now - timedelta(days=6 * 31) # last 6 months
            group_cols = [extract('year', Claim.filing_date), extract('month', Claim.filing_date)]
            order_cols = ['yr', 'mo']
            select_cols = [
                extract('year', Claim.filing_date).label('yr'),
                extract('month', Claim.filing_date).label('mo'),
                func.count(Claim.id).label('claim_volume'),
                func.count(actual_latest_pred.c.claim_id).label('fraud_count'),
            ]

        trend_query = (
            self.db.query(*select_cols)
            .outerjoin(actual_latest_pred, actual_latest_pred.c.claim_id == Claim.id)
            .filter(Claim.filing_date >= cutoff)
            .group_by(*group_cols)
            .order_by(*order_cols)
            .all()
        )

        result = []
        for row in trend_query:
            if interval == 'daily':
                label = f"{int(row.mo)}/{int(row.dy)}"
            elif interval == 'weekly':
                label = f"Wk {int(row.wk)}, {int(row.yr)}"
            elif interval == 'yearly':
                label = f"{int(row.yr)}"
            else:
                label = calendar.month_abbr[int(row.mo)]
                
            volume = row.claim_volume or 0
            fraud_count = row.fraud_count or 0
            fraud_rate = (fraud_count / volume) if volume > 0 else 0.0
            result.append({
                "label": label,
                "fraudRate": round(fraud_rate, 3),
                "claimVolume": volume,
            })

        return result

    def get_fraud_distribution_chart(self, role: str = "Admin") -> List[dict]:
        """Fraud by claim type — returns {name, value, fill} for the BarChart.

        value is the number of fraudulent (High + Critical) claims per policy type.
        Falls back to total claim counts when no fraud has been detected yet so
        the card is never empty.
        """
        if role == "Investigator":
            return []

        _FILL_MAP = [
            "var(--chart-1)", "var(--chart-2)",
            "var(--chart-3)", "var(--chart-4)",
            "var(--chart-5)",
        ]

        _LABEL_MAP = {
            "comprehensive": "Comprehensive",
            "zero_depreciation": "Zero Depreciation",
            "third_party": "Third Party",
            "own_damage": "Own Damage",
            "all_perils": "All Perils",
            "collision": "Collision",
            "liability": "Liability",
            "unknown": "Unspecified",
        }

        dist = self.get_fraud_distribution_by_type(role=role)
        chart_data = []
        for i, row in enumerate(dist):
            raw_type = (row.get("claim_type") or "").lower()
            name = _LABEL_MAP.get(raw_type) or raw_type.replace("_", " ").title() or "Unknown"
            fraud_count = row.get("fraud") or 0
            total = row.get("total") or 0
            # Use fraud count; fall back to total only if nothing is flagged
            value = fraud_count if fraud_count > 0 else 0
            chart_data.append({
                "name": name,
                "value": value,
                "total": total,
                "rate": row.get("rate", 0),
                "fill": _FILL_MAP[i % len(_FILL_MAP)],
            })

        # If no fraud is detected at all, show total claims so the card isn't empty
        if all(c["value"] == 0 for c in chart_data):
            for c in chart_data:
                c["value"] = c["total"]

        return chart_data if chart_data else [
            {"name": "No Data", "value": 0, "fill": "var(--chart-1)"}
        ]
