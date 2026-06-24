import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    identity_type = Column(String(50), nullable=True)
    identity_number = Column(String(100), nullable=True)
    dl_number = Column(String(100), nullable=True)
    dl_expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policies = relationship("Policy", back_populates="customer", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="customer")
    user = relationship("User", back_populates="customer", uselist=False)

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_number = Column(String(100), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    policy_holder_name = Column(String(200), nullable=True)
    policy_type = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    premium = Column(Float, nullable=False)
    deductible = Column(Float, nullable=False)
    coverage_limit = Column(Float, nullable=False)
    no_claim_bonus = Column(Float, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    customer = relationship("Customer", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vin = Column(String(17), unique=True, nullable=False, index=True)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    variant = Column(String(100), nullable=True)
    year = Column(Integer, nullable=False)
    purchase_year = Column(Integer, nullable=True)
    license_plate = Column(String(50), unique=True, nullable=False)
    color = Column(String(50), nullable=True)
    vehicle_type = Column(String(50), nullable=True)
    fuel_type = Column(String(50), nullable=True)
    transmission = Column(String(50), nullable=True)
    engine_number = Column(String(100), nullable=True)
    chassis_number = Column(String(100), nullable=True)
    purchase_price = Column(Float, nullable=True)
    current_market_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    claims = relationship("Claim", back_populates="vehicle")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String(100), unique=True, nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
    
    filing_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    reporting_delay_days = Column(Integer, nullable=True)
    status = Column(String(50), default="draft", nullable=False)
    workflow_status = Column(String(50), nullable=True)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policy = relationship("Policy", back_populates="claims")
    customer = relationship("Customer", back_populates="claims")
    vehicle = relationship("Vehicle", back_populates="claims")
    
    accident = relationship("Accident", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    financial_details = relationship("FinancialDetails", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    police_details = relationship("PoliceDetails", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    witnesses = relationship("Witness", back_populates="claim", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="claim", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="claim", cascade="all, delete-orphan")
    
    predictions = relationship("Prediction", back_populates="claim", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="claim", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_claims_status", "status"),
    )

class Accident(Base):
    __tablename__ = "accidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True)
    incident_date = Column(DateTime, nullable=False)
    incident_time = Column(String(50), nullable=True)
    accident_location = Column(String(500), nullable=True)
    gps_coordinates = Column(String(100), nullable=True)
    road_type = Column(String(100), nullable=True)
    road_condition = Column(String(100), nullable=True)
    weather_condition = Column(String(100), nullable=True)
    accident_description = Column(Text, nullable=True)
    vehicle_speed = Column(Integer, nullable=True)
    number_of_vehicles_involved = Column(Integer, nullable=True)
    number_of_injured = Column(Integer, nullable=True)
    fatalities = Column(Integer, nullable=True)
    
    claim = relationship("Claim", back_populates="accident")

class FinancialDetails(Base):
    __tablename__ = "financial_details"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True)
    claim_amount = Column(Float, nullable=False)
    repair_estimate = Column(Float, nullable=True)
    medical_expenses = Column(Float, nullable=True)
    hospital_charges = Column(Float, nullable=True)
    towing_charges = Column(Float, nullable=True)
    vehicle_recovery_charges = Column(Float, nullable=True)
    other_expenses = Column(Float, nullable=True)
    total_claim_amount = Column(Float, nullable=True)
    
    claim = relationship("Claim", back_populates="financial_details")

class PoliceDetails(Base):
    __tablename__ = "police_details"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True)
    police_report_available = Column(Boolean, default=False)
    fir_number = Column(String(100), nullable=True)
    police_station = Column(String(200), nullable=True)
    police_district = Column(String(100), nullable=True)
    officer_name = Column(String(100), nullable=True)
    officer_contact = Column(String(100), nullable=True)
    
    claim = relationship("Claim", back_populates="police_details")

class Witness(Base):
    __tablename__ = "witnesses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=True)
    phone = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    statement = Column(Text, nullable=True)
    identity_proof = Column(String(100), nullable=True)
    
    claim = relationship("Claim", back_populates="witnesses")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    verification_status = Column(String(50), nullable=True)
    verification_reasoning = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    claim = relationship("Claim", back_populates="documents")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=True)
    action = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    claim = relationship("Claim", back_populates="activity_logs")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_category = Column(String(50), nullable=False)
    prediction_confidence = Column(Float, nullable=False)
    shap_explanations = Column(JSON, nullable=True)
    rule_flags = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    base_ml_probability = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    claim = relationship("Claim", back_populates="predictions")


class Explanation(Base):
    __tablename__ = "explanations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    model_version = Column(String(100), nullable=False)
    shap_version = Column(String(50), nullable=False)
    base_value = Column(Float, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    top_positive_features = Column(JSON, nullable=True)
    top_negative_features = Column(JSON, nullable=True)
    shap_values = Column(JSON, nullable=True)
    visualization_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ExplanationCache(Base):
    __tablename__ = "explanation_cache"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True)
    explanation_id = Column(UUID(as_uuid=True), ForeignKey("explanations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

class FeatureMetadata(Base):
    __tablename__ = "feature_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feature_name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    explanation_template = Column(Text, nullable=False)
    importance_rank = Column(Integer, nullable=True)
    unit = Column(String(50), nullable=True)

class ModelExplanation(Base):
    __tablename__ = "model_explanations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(100), unique=True, nullable=False)
    global_importance_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ExplanationAuditLog(Base):
    __tablename__ = "explanation_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    explanation_id = Column(UUID(as_uuid=True), ForeignKey("explanations.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., 'generated', 'viewed', 'exported_pdf'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Investigation(Base):
    __tablename__ = "investigations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    investigator_id = Column(String(100), nullable=True)
    status = Column(String(50), default="assigned", nullable=False)
    notes = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    recommended_action = Column(String(255), nullable=True)
    final_recommendation_report = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    claim = relationship("Claim", back_populates="investigations")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False)
    performed_by = Column(String(100), nullable=False)
    target_table = Column(String(100), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_action", "action"),
    )

class PipelineVersion(Base):
    __tablename__ = "pipeline_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=False)
    encoder_path = Column(String(255), nullable=False)
    scaler_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)



class PreprocessingLog(Base):
    __tablename__ = "preprocessing_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    missing_values_imputed = Column(Integer, default=0)
    features_engineered = Column(Integer, default=0)
    warnings = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    claim = relationship("Claim")

# --- PHASE 9: KNOWLEDGE BASE & RAG ---

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False) # PDF, DOCX, TXT, etc.
    source_path = Column(String(500), nullable=True) # File path or URL
    author = Column(String(100), nullable=True)
    version = Column(String(50), default="1.0")
    language = Column(String(10), default="en")
    status = Column(String(50), default="active") # active, archived
    
    category_id = Column(Integer, ForeignKey("knowledge_categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding_version = Column(String(50), nullable=True)
    
    document = relationship("KnowledgeDocument", backref="chunks")

class KnowledgeTag(Base):
    __tablename__ = "knowledge_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

class DocumentTagLink(Base):
    __tablename__ = "document_tag_links"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("knowledge_tags.id", ondelete="CASCADE"), primary_key=True)

class RetrievalHistory(Base):
    __tablename__ = "retrieval_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    top_k_returned = Column(Integer, nullable=False)
    retrieved_chunk_ids = Column(JSON, nullable=False) # List of chunk IDs returned
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# --- PHASE 10: AI INVESTIGATION AGENT ---

class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True)
    report_version_id = Column(UUID(as_uuid=True), nullable=True) # Linked to ReportVersion
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="draft") # draft, pending_review, approved, rejected
    approval_status = Column(String(50), nullable=True)
    locked_after_approval = Column(Boolean, default=False)
    
    # Executive Summary (Section 2)
    executive_summary = Column(Text, nullable=True)
    fraud_probability = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=True)
    final_ai_recommendation = Column(String(200), nullable=True)
    
    # Machine Learning Prediction (Section 4)
    ml_prediction_details = Column(JSON, nullable=True)
    
    # SHAP Explainability (Section 5)
    shap_explainability = Column(JSON, nullable=True)
    
    # Knowledge Base Findings (Section 6)
    knowledge_base_findings = Column(JSON, nullable=True)
    
    # Policy Compliance Analysis (Section 7)
    policy_compliance_analysis = Column(JSON, nullable=True)
    
    # Historical Claim Analysis (Section 8)
    historical_claim_analysis = Column(JSON, nullable=True)
    
    # Contradiction Analysis (Section 9)
    contradiction_analysis = Column(JSON, nullable=True)
    
    # Risk Assessment (Section 10)
    risk_assessment = Column(JSON, nullable=True)
    
    # Investigation Recommendations (Section 11)
    investigation_recommendations = Column(JSON, nullable=True)
    
    # Evidence Checklist (Section 12)
    evidence_checklist = Column(JSON, nullable=True)
    
    # Supporting Evidence (Section 13)
    supporting_evidence = Column(JSON, nullable=True)
    
    # Confidence Analysis (Section 14)
    confidence_analysis = Column(JSON, nullable=True)
    
    # Human Review (Section 16)
    human_review = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    claim = relationship("Claim", backref="investigation_report")
    versions = relationship("ReportVersion", back_populates="report", cascade="all, delete-orphan")
    signatures = relationship("DigitalSignature", back_populates="report", cascade="all, delete-orphan")
    comments = relationship("ReportComment", back_populates="report", cascade="all, delete-orphan")

# --- PHASE 12: ENTERPRISE REPORTING & EVIDENCE MANAGEMENT ---

class ReportVersion(Base):
    __tablename__ = "report_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    generated_by = Column(String(100), nullable=True)
    modified_by = Column(String(100), nullable=True)
    reason_for_revision = Column(Text, nullable=True)
    report_data_snapshot = Column(JSON, nullable=False) # Full snapshot of the report fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    report = relationship("InvestigationReport", back_populates="versions")

class DigitalEvidence(Base):
    __tablename__ = "digital_evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(100), nullable=False) # e.g., "user_upload", "police_api", "agent_retrieval"
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False) # SHA-256 Hash
    verification_status = Column(String(50), default="unverified")
    integrity_status = Column(String(50), default="intact")
    version = Column(Integer, default=1)
    chain_of_custody_log = Column(JSON, nullable=True) # Array of custody events
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ReportTemplate(Base):
    __tablename__ = "report_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False) # e.g., "Enterprise", "Executive"
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False) # Jinja2 or Markdown template content
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DigitalSignature(Base):
    __tablename__ = "digital_signatures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False)
    signer_id = Column(String(100), nullable=False)
    signer_role = Column(String(50), nullable=False)
    signature_hash = Column(String(255), nullable=False)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    report = relationship("InvestigationReport", back_populates="signatures")

class ReportComment(Base):
    __tablename__ = "report_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(100), nullable=False)
    section = Column(String(100), nullable=True) # Which section the comment is for
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    report = relationship("InvestigationReport", back_populates="comments")

class ExportQueue(Base):
    __tablename__ = "export_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False)
    format = Column(String(20), nullable=False) # pdf, docx, html
    status = Column(String(50), default="pending") # pending, processing, completed, failed
    file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    requested_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

class DownloadHistory(Base):
    __tablename__ = "download_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(100), nullable=False)
    format = Column(String(20), nullable=False)
    ip_address = Column(String(45), nullable=True)
    downloaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ExportAnalytics(Base):
    __tablename__ = "export_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    format = Column(String(20), nullable=False)
    count = Column(Integer, default=0)
    last_exported_at = Column(DateTime, nullable=True)

class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String(100), nullable=False) # For LangGraph Memory checkpointing
    status = Column(String(50), nullable=False) # running, paused_hitl, completed, failed
    latency_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AgentAudit(Base):
    __tablename__ = "agent_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False) # e.g., "report_generated", "human_approved", "human_rejected"
    user_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DashboardSnapshot(Base):
    __tablename__ = "dashboard_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date = Column(Date, default=datetime.utcnow().date, nullable=False)
    total_claims = Column(Integer, default=0)
    fraud_predictions = Column(Integer, default=0)
    completed_investigations = Column(Integer, default=0)
    open_investigations = Column(Integer, default=0)
    investigator_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ModelPerformanceHistory(Base):
    __tablename__ = "model_performance_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(50), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class AgentExecutionAnalytics(Base):
    __tablename__ = "agent_execution_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    token_usage = Column(Integer, default=0)
    latency_ms = Column(Float, nullable=True)
    failures = Column(Integer, default=0)
    retries = Column(Integer, default=0)
    hallucination_rate = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class DashboardCache(Base):
    __tablename__ = "dashboard_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_key = Column(String(100), unique=True, nullable=False)
    dashboard_json = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

class AnalyticsAuditLog(Base):
    __tablename__ = "analytics_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)
    dashboard_viewed = Column(String(100), nullable=False)
    filters_applied = Column(JSON, nullable=True)
    exported_format = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# --- PHASE 14: ENTERPRISE AUTHENTICATION & SECURITY ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(100), unique=True, nullable=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    status = Column(String(50), default="Active", nullable=False) # Active, Suspended, Archived, Deleted
    mfa_secret = Column(String(255), nullable=True) # TOTP secret
    mfa_enabled = Column(Boolean, default=False)
    force_password_change = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="user")

class PasswordHistory(Base):
    __tablename__ = "password_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="password_history")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False) # e.g. claim.read, report.export
    description = Column(Text, nullable=True)
    
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    
    jti = Column(String(255), primary_key=True) # JWT ID
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Nullable for failed logins with unknown users
    username_attempted = Column(String(255), nullable=True)
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    browser = Column(String(255), nullable=True)
    device = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False) # e.g. login_failed, account_locked, password_changed
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_security_events_timestamp", "timestamp"),
        Index("idx_security_events_type", "event_type"),
    )

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False) # e.g. "Background Worker"
    key_hash = Column(String(255), nullable=False, unique=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# --- PHASE 16: CONTINUOUS LEARNING & FRAUD INTELLIGENCE ---

class InvestigatorFeedback(Base):
    __tablename__ = "investigator_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    investigator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    final_decision = Column(String(100), nullable=False) # e.g., "Fraud Confirmed", "Genuine Claim"
    investigation_notes = Column(Text, nullable=True)
    investigation_duration_hours = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    claim = relationship("Claim", backref="feedback")
    investigator = relationship("User")

class PredictionEvaluation(Base):
    __tablename__ = "prediction_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    ground_truth = Column(Integer, nullable=False) # 1 for fraud, 0 for legitimate
    predicted_label = Column(Integer, nullable=False) # 1 for fraud, 0 for legitimate
    is_correct = Column(Boolean, nullable=False)
    error_type = Column(String(50), nullable=False) # "TP", "TN", "FP", "FN"
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    prediction = relationship("Prediction", backref="evaluation")
    reviewer = relationship("User")

class CaseResolution(Base):
    __tablename__ = "case_resolutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    fraud_confirmed = Column(Boolean, nullable=False)
    claim_approved = Column(Boolean, nullable=False)
    resolution_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    claim = relationship("Claim", backref="resolution")


class KnownPolicy(Base):
    """Whitelist of known-valid insurance policy numbers.
    Seeded from fraud_rules/policy.txt. Any claim whose policy_number
    is NOT in this table is flagged as potential fraud."""

    __tablename__ = "known_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_number = Column(String(100), unique=True, nullable=False, index=True)
    insurer = Column(String(100), nullable=True)
    policy_type = Column(String(50), nullable=True)
    holder_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class KnownVehicle(Base):
    """Whitelist of known-valid vehicle registration plates.
    Seeded from fraud_rules/vehicle.txt. Any claim whose license_plate
    is NOT in this table is flagged as potential fraud."""

    __tablename__ = "known_vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_plate = Column(String(50), unique=True, nullable=False, index=True)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    owner_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
