import json
import csv
from io import StringIO
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.models import AnalyticsAuditLog

class AnalyticsAuditLogger:
    def __init__(self, db: Session):
        self.db = db

    def log_view(self, user_id: str, dashboard_viewed: str, filters: Dict[str, Any] = None):
        log_entry = AnalyticsAuditLog(
            user_id=user_id,
            dashboard_viewed=dashboard_viewed,
            filters_applied=filters
        )
        self.db.add(log_entry)
        self.db.commit()

    def log_export(self, user_id: str, dashboard_viewed: str, export_format: str, filters: Dict[str, Any] = None):
        log_entry = AnalyticsAuditLog(
            user_id=user_id,
            dashboard_viewed=dashboard_viewed,
            filters_applied=filters,
            exported_format=export_format
        )
        self.db.add(log_entry)
        self.db.commit()


class AnalyticsExportService:
    @staticmethod
    def export_csv(data: Dict[str, Any], section: str) -> str:
        # A simple recursive flattener to extract list data from a given section (e.g., 'geographic_analytics')
        if section not in data:
            return ""
            
        section_data = data[section]
        if not isinstance(section_data, list) or len(section_data) == 0:
            return ""

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=section_data[0].keys())
        writer.writeheader()
        writer.writerows(section_data)
        
        return output.getvalue()
