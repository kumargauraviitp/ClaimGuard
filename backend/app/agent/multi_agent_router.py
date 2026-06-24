from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel
from typing import Optional
import uuid

from .graph import multi_agent_graph
from app.models import AgentExecution, InvestigationReport

router = APIRouter(prefix="/multi-agent", tags=["Multi-Agent AI Investigation"])

class InvestigateRequest(BaseModel):
    claim_id: str

class ApproveRequest(BaseModel):
    thread_id: str
    feedback: Optional[str] = None
    approved: bool = True

@router.post("/investigate")
def investigate_claim(request: InvestigateRequest, db: Session = Depends(get_db)):
    """
    Kicks off the Phase 11 Multi-Agent System.
    Runs until the HITL breakpoint (before saving report).
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initialize state
    initial_state = {
        "claim_id": request.claim_id,
        "thread_id": thread_id,
        "status": "running",
        "errors": []
    }
    
    # Create execution log
    exec_log = AgentExecution(
        claim_id=request.claim_id,
        thread_id=thread_id,
        status="running"
    )
    db.add(exec_log)
    db.commit()
    
    try:
        # Run graph (stops at "StoreReport" due to interrupt)
        # We can stream events via `multi_agent_graph.stream` for event-driven orchestration
        # For HTTP POST, we typically wait or return immediate. We'll wait here.
        result = multi_agent_graph.invoke(initial_state, config=config)
        
        exec_log.status = "paused_hitl"
        db.commit()
        
        return {
            "status": "pending_human_review",
            "thread_id": thread_id,
            "draft_report": result.get("draft_report"),
            "qa_feedback_history": result.get("qa_feedback")
        }
    except Exception as e:
        exec_log.status = "failed"
        exec_log.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{thread_id}")
def get_status(thread_id: str, db: Session = Depends(get_db)):
    """Get the event-driven execution status of a thread."""
    exec_log = db.query(AgentExecution).filter(AgentExecution.thread_id == thread_id).first()
    if not exec_log:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    config = {"configurable": {"thread_id": thread_id}}
    state = multi_agent_graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "db_status": exec_log.status,
        "next_node": state.next,
        "errors": state.values.get("errors", [])
    }

@router.post("/approve")
def approve_report(request: ApproveRequest, db: Session = Depends(get_db)):
    """
    HITL Continuation. Human reviews the draft report and approves it.
    The Multi-Agent System resumes and stores the final versioned report.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    current_state = multi_agent_graph.get_state(config)
    if not current_state.next:
        raise HTTPException(status_code=400, detail="Graph is not paused or does not exist.")
        
    multi_agent_graph.update_state(config, {"human_feedback": request.feedback})
    
    if request.approved:
        # Resume Execution
        result = multi_agent_graph.invoke(None, config=config)
        
        exec_log = db.query(AgentExecution).filter(AgentExecution.thread_id == request.thread_id).first()
        if exec_log:
            exec_log.status = "completed"
            db.commit()
            
        return {
            "status": "approved_and_stored",
            "report_id": result.get("final_report_id")
        }
    else:
        exec_log = db.query(AgentExecution).filter(AgentExecution.thread_id == request.thread_id).first()
        if exec_log:
            exec_log.status = "human_rejected"
            db.commit()
        return {"status": "rejected"}

@router.get("/report/{claim_id}")
def get_report(claim_id: str, db: Session = Depends(get_db)):
    """Fetches the approved Investigation Report for the claim."""
    report = db.query(InvestigationReport).filter(
        InvestigationReport.claim_id == claim_id,
        InvestigationReport.status == "approved"
    ).order_by(InvestigationReport.version.desc()).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="No approved report found for this claim.")
        
    return report
