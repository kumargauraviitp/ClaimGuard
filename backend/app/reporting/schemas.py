from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- Digital Evidence ---
class DigitalEvidenceBase(BaseModel):
    source: str
    file_name: str
    file_hash: str
    verification_status: str
    integrity_status: str

class DigitalEvidenceResponse(DigitalEvidenceBase):
    id: UUID4
    claim_id: UUID4
    file_path: str
    version: int
    chain_of_custody_log: Optional[List[Dict[str, Any]]] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Comments ---
class ReportCommentCreate(BaseModel):
    section: Optional[str] = None
    content: str

class ReportCommentResponse(BaseModel):
    id: UUID4
    report_id: UUID4
    user_id: str
    section: Optional[str]
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Digital Signature ---
class DigitalSignatureRequest(BaseModel):
    pass

class DigitalSignatureResponse(BaseModel):
    id: UUID4
    report_id: UUID4
    signer_id: str
    signer_role: str
    signature_hash: str
    signed_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Investigation Report Core ---
class InvestigationReportBase(BaseModel):
    version: int
    status: str
    approval_status: Optional[str] = None
    locked_after_approval: Optional[bool] = False

    executive_summary: Optional[str] = None
    fraud_probability: Optional[float] = None
    confidence_score: Optional[float] = None
    risk_level: Optional[str] = None
    final_ai_recommendation: Optional[str] = None

    ml_prediction_details: Optional[Dict[str, Any]] = None
    shap_explainability: Optional[Dict[str, Any]] = None
    knowledge_base_findings: Optional[Dict[str, Any]] = None
    policy_compliance_analysis: Optional[Dict[str, Any]] = None
    historical_claim_analysis: Optional[Dict[str, Any]] = None
    contradiction_analysis: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    investigation_recommendations: Optional[Dict[str, Any]] = None
    evidence_checklist: Optional[Dict[str, Any]] = None
    supporting_evidence: Optional[Dict[str, Any]] = None
    confidence_analysis: Optional[Dict[str, Any]] = None
    human_review: Optional[Dict[str, Any]] = None

class InvestigationReportResponse(InvestigationReportBase):
    id: UUID4
    claim_id: UUID4
    report_version_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    
    signatures: List[DigitalSignatureResponse] = []
    comments: List[ReportCommentResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ReportVersionResponse(BaseModel):
    id: UUID4
    report_id: UUID4
    revision_number: int
    generated_by: Optional[str]
    modified_by: Optional[str]
    reason_for_revision: Optional[str]
    created_at: datetime
    report_data_snapshot: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

# --- Export & Analytics ---
class ExportQueueRequest(BaseModel):
    format: str

class ExportQueueResponse(BaseModel):
    id: UUID4
    report_id: UUID4
    format: str
    status: str
    error_message: Optional[str]
    requested_by: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ReportDiffResponse(BaseModel):
    report_id: UUID4
    version_1: int
    version_2: int
    diff_summary: Dict[str, Any]
    detailed_diff: Dict[str, Any]
class PaginatedResponse(BaseModel):
    items: List['InvestigationReportResponse']
    total: int
    page: int
    size: int
    pages: int

