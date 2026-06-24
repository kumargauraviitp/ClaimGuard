"""
Documents router — handles file uploads for claims, extracts text,
and runs AI verification.

Endpoints:
- POST /api/claims/{claim_id}/documents  — upload a document
- GET  /api/claims/{claim_id}/documents  — list documents for a claim
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Claim, Document
from app.auth.permission_service import get_current_user_or_api_key
from app.documents.processor import extract_text_from_file, verify_document_with_ai

router = APIRouter()

# Storage directory for uploaded documents
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "documents")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx", ".txt"}


@router.post("/claims/{claim_id}/documents")
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("any"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_api_key),
):
    """Upload a document for a claim. Extracts text and runs AI verification."""
    # Verify claim exists
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Validate file extension
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save the file
    claim_dir = os.path.join(STORAGE_DIR, claim_id)
    os.makedirs(claim_dir, exist_ok=True)
    saved_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(claim_dir, saved_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text
    extracted_text = extract_text_from_file(file_path, filename)

    # Run AI verification
    claim_context = {
        "vehicle_make": claim.vehicle.make if claim.vehicle else "",
        "claim_amount": claim.financial_details.claim_amount if claim.financial_details else 0,
    }
    verification = verify_document_with_ai(extracted_text, document_type, claim_context)

    # Save document record to DB
    doc = Document(
        claim_id=claim_id,
        document_type=document_type,
        file_name=filename,
        file_path=file_path,
        verification_status=verification.get("status", "unverified"),
        verification_reasoning=verification.get("reasoning", ""),
        extracted_text=extracted_text[:10000] if extracted_text else None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "claim_id": claim_id,
        "file_name": filename,
        "document_type": document_type,
        "verification": verification,
        "extracted_text_preview": extracted_text[:500] if extracted_text else "",
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else datetime.utcnow().isoformat(),
    }


@router.get("/claims/{claim_id}/documents")
def list_documents(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_api_key),
):
    """List all documents uploaded for a claim."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    docs = db.query(Document).filter(Document.claim_id == claim_id).all()
    return [
        {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "document_type": doc.document_type,
            "file_path": doc.file_path,
            "uploaded_at": doc.created_at.isoformat() if hasattr(doc, 'created_at') else None,
        }
        for doc in docs
    ]
