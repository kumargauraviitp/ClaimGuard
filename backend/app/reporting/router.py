import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.reporting.schemas import (
    InvestigationReportResponse, 
    PaginatedResponse, 
    ReportDiffResponse,
    DigitalEvidenceResponse,
    DigitalSignatureResponse,
    ExportQueueRequest,
    ExportQueueResponse
)
from app.reporting.rbac import require_role, require_permission, UserContext
from app.reporting.report_builder import ReportBuilder
from app.reporting.workflow_manager import WorkflowManager
from app.reporting.search_engine import ReportSearchEngine
from app.reporting.export_service import ExportService
from app.reporting.evidence_manager import EvidenceManager
from app.models import ExportQueue

router = APIRouter(prefix="/api/reports", tags=["Enterprise Reporting"])

@router.post("/generate", response_model=InvestigationReportResponse)
def generate_report(
    claim_id: uuid.UUID,
    ai_payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("write"))
):
    builder = ReportBuilder(db)
    report = builder.build_report(claim_id, ai_payload, user.user_id)
    return report

@router.get("/search", response_model=PaginatedResponse)
def search_reports(
    query: str,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("read"))
):
    engine = ReportSearchEngine(db)
    return engine.search_reports(query, page, size)

@router.post("/{report_id}/approve", response_model=DigitalSignatureResponse)
def approve_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role(["manager", "auditor"]))
):
    manager = WorkflowManager(db)
    signature = manager.approve_and_sign_report(report_id, user.user_id, user.role)
    return signature

@router.post("/{report_id}/export", response_model=ExportQueueResponse)
def export_report(
    report_id: uuid.UUID,
    request: ExportQueueRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("export"))
):
    if request.format not in ["pdf", "docx", "html"]:
        raise HTTPException(status_code=400, detail="Unsupported format")
        
    job = ExportQueue(
        report_id=report_id,
        format=request.format,
        requested_by=user.user_id
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    service = ExportService(db)
    background_tasks.add_task(service.process_export_job, job.id)
    
    return job

@router.get("/{report_id}/diff", response_model=ReportDiffResponse)
def get_report_diff(
    report_id: uuid.UUID,
    v1: int,
    v2: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("read"))
):
    from app.reporting.version_diff import VersionDiffEngine
    engine = VersionDiffEngine(db)
    return engine.compute_diff(report_id, v1, v2)

@router.post("/evidence/upload", response_model=DigitalEvidenceResponse)
async def upload_evidence(
    claim_id: uuid.UUID = Form(...),
    source: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("write"))
):
    manager = EvidenceManager(db)
    evidence = await manager.upload_evidence(claim_id, file, source, user.user_id)
    return evidence
