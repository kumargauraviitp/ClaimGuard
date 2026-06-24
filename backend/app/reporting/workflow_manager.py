import uuid
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import InvestigationReport, DigitalSignature, ReportVersion
from app.reporting.audit_trail import log_audit_event

class WorkflowManager:
    def __init__(self, db: Session):
        self.db = db

    def snapshot_report(self, report: InvestigationReport, user_id: str, reason: str):
        # Create a report version (Snapshot) before making changes or locking
        snapshot = {
            "executive_summary": report.executive_summary,
            "risk_level": report.risk_level,
            "fraud_probability": report.fraud_probability,
            "confidence_score": report.confidence_score,
            "shap_explainability": report.shap_explainability,
            "version": report.version
        }
        report_version = ReportVersion(
            report_id=report.id,
            revision_number=report.version,
            generated_by=user_id,
            reason_for_revision=reason,
            report_data_snapshot=snapshot
        )
        self.db.add(report_version)
        self.db.commit()

    def approve_and_sign_report(self, report_id: uuid.UUID, user_id: str, role: str) -> DigitalSignature:
        report = self.db.query(InvestigationReport).filter(InvestigationReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report.locked_after_approval:
            raise HTTPException(status_code=400, detail="Report is already locked and approved.")

        # Digital Signature Hash (Mocking signature payload based on current report version and time)
        payload = f"{report.id}-{report.version}-{user_id}-{datetime.utcnow().isoformat()}"
        signature_hash = hashlib.sha256(payload.encode()).hexdigest()

        signature = DigitalSignature(
            report_id=report.id,
            signer_id=user_id,
            signer_role=role,
            signature_hash=signature_hash
        )
        self.db.add(signature)

        report.approval_status = "approved"
        report.status = "approved"
        report.locked_after_approval = True

        self.snapshot_report(report, user_id, "Snapshot created upon approval")
        self.db.commit()

        # Audit event
        log_audit_event(
            self.db, 
            claim_id=report.claim_id, 
            action="report_approved_and_signed", 
            user_id=user_id, 
            details={"report_id": str(report.id), "signature_hash": signature_hash}
        )

        return signature
