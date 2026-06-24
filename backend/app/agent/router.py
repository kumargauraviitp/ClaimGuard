from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel
from typing import Optional
import uuid

from .graph import multi_agent_graph as agent_graph
from app.models import AgentExecution, InvestigationReport

router = APIRouter(prefix="/agent", tags=["AI Investigation Agent"])

class InvestigateRequest(BaseModel):
    claim_id: str

class ApproveRequest(BaseModel):
    thread_id: str
    feedback: Optional[str] = None
    approved: bool = True

@router.post("/investigate")
def investigate_claim(request: InvestigateRequest, db: Session = Depends(get_db)):
    """
    Kicks off the Phase 10 LangGraph.
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
        result = agent_graph.invoke(initial_state, config=config)
        
        exec_log.status = "paused_hitl"
        db.commit()
        
        return {
            "status": "pending_human_review",
            "thread_id": thread_id,
            "draft_report": result.get("draft_report")
        }
    except Exception as e:
        exec_log.status = "failed"
        exec_log.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve")
def approve_report(request: ApproveRequest, db: Session = Depends(get_db)):
    """
    HITL Continuation. Human reviews the draft report and approves it.
    The LangGraph resumes and stores the final versioned report.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # Retrieve current state from Checkpointer
    current_state = agent_graph.get_state(config)
    if not current_state.next:
        raise HTTPException(status_code=400, detail="Graph is not paused or does not exist.")
        
    # Update State with feedback if provided
    agent_graph.update_state(config, {"human_feedback": request.feedback})
    
    if request.approved:
        # Resume Execution
        result = agent_graph.invoke(None, config=config)
        
        # Update Execution Log
        exec_log = db.query(AgentExecution).filter(AgentExecution.thread_id == request.thread_id).first()
        if exec_log:
            exec_log.status = "completed"
            db.commit()
            
        return {
            "status": "approved_and_stored",
            "report_id": result.get("final_report_id")
        }
    else:
        # If rejected, we don't proceed to StoreReport, we just fail it
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
