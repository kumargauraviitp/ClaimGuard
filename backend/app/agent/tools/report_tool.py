from sqlalchemy.orm import Session
from app.models import InvestigationReport, AgentAudit

def store_report(db: Session, claim_id: str, report_data: dict, status: str = "pending_review") -> str:
    # Check if exists
    existing = db.query(InvestigationReport).filter(InvestigationReport.claim_id == claim_id).first()
    
    if existing:
        existing.version += 1
        existing.status = status
        existing.summary = report_data.get("summary", "")
        existing.risk_level = report_data.get("risk_level", "Unknown")
        existing.confidence_score = report_data.get("confidence_score")
        existing.shap_analysis = report_data.get("shap_analysis")
        existing.policy_references = report_data.get("policy_references", [])
        existing.missing_documents = report_data.get("missing_documents", [])
        existing.suspicious_indicators = report_data.get("suspicious_indicators", [])
        existing.investigation_checklist = report_data.get("investigation_checklist", [])
        existing.follow_up_questions = report_data.get("follow_up_questions", [])
        existing.citations = report_data.get("citations", [])
        report_id = str(existing.id)
        version = existing.version
    else:
        new_report = InvestigationReport(
            claim_id=claim_id,
            status=status,
            summary=report_data.get("summary", ""),
            risk_level=report_data.get("risk_level", "Unknown"),
            confidence_score=report_data.get("confidence_score"),
            shap_analysis=report_data.get("shap_analysis"),
            policy_references=report_data.get("policy_references", []),
            missing_documents=report_data.get("missing_documents", []),
            suspicious_indicators=report_data.get("suspicious_indicators", []),
            investigation_checklist=report_data.get("investigation_checklist", []),
            follow_up_questions=report_data.get("follow_up_questions", []),
            citations=report_data.get("citations", [])
        )
        db.add(new_report)
        db.flush()
        report_id = str(new_report.id)
        version = 1
        
    audit = AgentAudit(
        claim_id=claim_id,
        action="report_generated",
        details={"version": version, "status": status}
    )
    db.add(audit)
    db.commit()
    
    return report_id
