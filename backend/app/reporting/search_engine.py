from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import InvestigationReport

class ReportSearchEngine:
    def __init__(self, db: Session):
        self.db = db

    def search_reports(self, query: str, page: int = 1, size: int = 10):
        # Basic ILIKE search (Can be expanded to PostgreSQL tsvector)
        offset = (page - 1) * size
        base_query = self.db.query(InvestigationReport).filter(
            or_(
                InvestigationReport.executive_summary.ilike(f"%{query}%"),
                InvestigationReport.risk_level.ilike(f"%{query}%"),
            )
        )
        total = base_query.count()
        items = base_query.offset(offset).limit(size).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
