import uuid
from sqlalchemy.orm import Session
from app.models import InvestigationReport, Claim
from app.reporting.section_generator import SectionGenerator
from app.reporting.audit_trail import log_audit_event

class ReportBuilder:
    def __init__(self, db: Session):
        self.db = db
        self.section_generator = SectionGenerator()

    def build_report(self, claim_id: uuid.UUID, ai_payload: dict, user_id: str) -> InvestigationReport:
        # Check if report exists
        report = self.db.query(InvestigationReport).filter(InvestigationReport.claim_id == claim_id).first()
        
        if report and report.locked_after_approval:
            raise ValueError("Cannot rebuild a report that has been locked after approval.")
            
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError("Claim not found")

        claim_amount = float(claim.financial_details.total_claim_amount) if claim.financial_details and claim.financial_details.total_claim_amount else 0.0
        claim_data = {"claim_id": str(claim.id), "claim_amount": claim_amount}
        
        executive_summary = self.section_generator.generate_executive_summary(claim_data, ai_payload)
        confidence_analysis = self.section_generator.generate_ai_confidence_explanation(
            ai_payload.get("shap_analysis", {}), 
            ai_payload
        )
        timeline = self.section_generator.generate_investigation_timeline(ai_payload.get("events", []))
        
        if not report:
            report = InvestigationReport(claim_id=claim_id)
            self.db.add(report)
        else:
            report.version += 1

        report.executive_summary = executive_summary
        report.fraud_probability = ai_payload.get("fraud_probability", 0.0)
        report.confidence_score = ai_payload.get("confidence_score", 0.0)
        report.risk_level = ai_payload.get("risk_level", "low")
        report.final_ai_recommendation = ai_payload.get("recommendation", "Approve Claim")
        
        report.shap_explainability = ai_payload.get("shap_analysis", {})
        report.ml_prediction_details = {"timeline": timeline}
        report.confidence_analysis = confidence_analysis
        report.status = "draft"
        report.approval_status = "pending"
        report.locked_after_approval = False
        
        self.db.commit()
        self.db.refresh(report)

        # Log creation
        log_audit_event(
            self.db, 
            claim_id=claim_id, 
            action="report_generated", 
            user_id=user_id, 
            details={"report_id": str(report.id), "version": report.version}
        )
        
        return report
