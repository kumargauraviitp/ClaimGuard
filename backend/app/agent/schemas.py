from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- LLM OUTPUT SCHEMAS ---

class InvestigationChecklistItem(BaseModel):
    task: str = Field(description="The specific action the investigator needs to perform.")
    reason: str = Field(description="Why this action is necessary based on the claim facts and ML prediction.")
    priority: str = Field(description="High, Medium, or Low")

class FollowUpQuestion(BaseModel):
    question: str = Field(description="A question the investigator should ask the claimant or workshop.")
    target: str = Field(description="Who to ask (e.g., Claimant, Workshop, Police).")

class Citation(BaseModel):
    source_title: str
    version: str
    relevant_excerpt: str

class FinalInvestigationReport(BaseModel):
    """The strict JSON schema the LLM must generate for the final report."""
    summary: str = Field(description="Executive summary of the investigation analysis.")
    risk_level: str = Field(description="Low, Medium, High, or Critical")
    confidence_score: float = Field(description="A score between 0.0 and 1.0 indicating confidence in the analysis.")
    
    shap_analysis: str = Field(description="A human-readable interpretation of the ML SHAP explanation.")
    policy_references: List[str] = Field(description="List of relevant policy clauses governing this claim.")
    
    missing_documents: List[str] = Field(description="Required documents that are missing from the claim.")
    suspicious_indicators: List[str] = Field(description="Anomalies detected in the claim data, ML prediction, or SHAP values.")
    
    investigation_checklist: List[InvestigationChecklistItem]
    follow_up_questions: List[FollowUpQuestion]
    
    citations: List[Citation] = Field(description="Exact citations from retrieved knowledge used to support this report.")

# --- LANGGRAPH MULTI-AGENT STATE ---

class AgentState(TypedDict):
    """The Shared Agent Memory for the Multi-Agent System."""
    
    # Core Orchestration
    claim_id: str
    thread_id: str
    status: str # running, pending_review, completed, failed
    errors: List[str]
    
    # Parallel Input Agent Outputs
    claim_analysis: Dict[str, Any]
    prediction_analysis: Dict[str, Any]
    shap_analysis: Dict[str, Any]
    knowledge_context: Dict[str, Any]
    policy_compliance: Dict[str, Any]
    claim_history: Dict[str, Any]
    
    # Synthesizing Agent Outputs
    contradictions: Dict[str, Any]
    risk_assessment: Dict[str, Any] # Includes confidence aggregation
    recommendations: Dict[str, Any]
    
    # Advanced Cognitive
    reflection: str # Output from Reflection Agent
    qa_feedback: Optional[str] # Output from Quality Assurance Agent (forces loop if failed)
    
    # Output & HITL
    draft_report: Optional[FinalInvestigationReport]
    human_feedback: Optional[str] # From Human Approval Node
    final_report_id: Optional[str]
