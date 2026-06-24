import uuid
import difflib
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import ReportVersion

class VersionDiffEngine:
    def __init__(self, db: Session):
        self.db = db

    def compute_diff(self, report_id: uuid.UUID, v1_num: int, v2_num: int) -> dict:
        v1 = self.db.query(ReportVersion).filter(
            ReportVersion.report_id == report_id, 
            ReportVersion.revision_number == v1_num
        ).first()
        v2 = self.db.query(ReportVersion).filter(
            ReportVersion.report_id == report_id, 
            ReportVersion.revision_number == v2_num
        ).first()

        if not v1 or not v2:
            raise HTTPException(status_code=404, detail="One or both report versions not found")

        diff_summary = {}
        detailed_diff = {}

        # Compare top-level keys
        all_keys = set(v1.report_data_snapshot.keys()).union(set(v2.report_data_snapshot.keys()))
        for key in all_keys:
            val1 = str(v1.report_data_snapshot.get(key, ""))
            val2 = str(v2.report_data_snapshot.get(key, ""))

            if val1 != val2:
                diff_summary[key] = "Changed"
                
                # Compute line-by-line diff
                diff_lines = list(difflib.unified_diff(
                    val1.splitlines(),
                    val2.splitlines(),
                    lineterm='',
                    fromfile=f"v{v1_num}",
                    tofile=f"v{v2_num}"
                ))
                detailed_diff[key] = "\n".join(diff_lines)
            else:
                diff_summary[key] = "Unchanged"

        return {
            "report_id": report_id,
            "version_1": v1_num,
            "version_2": v2_num,
            "diff_summary": diff_summary,
            "detailed_diff": detailed_diff
        }
