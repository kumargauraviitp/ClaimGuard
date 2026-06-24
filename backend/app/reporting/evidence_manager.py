import hashlib
import uuid
import os
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models import DigitalEvidence
from app.reporting.audit_trail import log_audit_event

EVIDENCE_STORAGE_DIR = "storage/evidence"
os.makedirs(EVIDENCE_STORAGE_DIR, exist_ok=True)

class EvidenceManager:
    def __init__(self, db: Session):
        self.db = db

    def calculate_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def upload_evidence(self, claim_id: uuid.UUID, file: UploadFile, source: str, user_id: str) -> DigitalEvidence:
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(EVIDENCE_STORAGE_DIR, unique_filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        file_hash = self.calculate_hash(file_path)

        chain_of_custody = [{
            "event": "uploaded",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "hash": file_hash
        }]

        evidence = DigitalEvidence(
            claim_id=claim_id,
            source=source,
            file_name=file.filename,
            file_path=file_path,
            file_hash=file_hash,
            verification_status="uploaded",
            integrity_status="intact",
            chain_of_custody_log=chain_of_custody
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        # Log to Immutable Audit Trail
        log_audit_event(
            db=self.db,
            claim_id=claim_id,
            action="evidence_uploaded",
            user_id=user_id,
            details={"evidence_id": str(evidence.id), "file_name": evidence.file_name, "hash": file_hash}
        )

        return evidence

    def verify_integrity(self, evidence_id: uuid.UUID) -> bool:
        evidence = self.db.query(DigitalEvidence).filter(DigitalEvidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")

        current_hash = self.calculate_hash(evidence.file_path)
        is_intact = (current_hash == evidence.file_hash)

        if evidence.integrity_status != ("intact" if is_intact else "corrupted"):
            evidence.integrity_status = "intact" if is_intact else "corrupted"
            
            # Update the chain of custody log
            log_entry = {
                "event": "integrity_check",
                "timestamp": datetime.utcnow().isoformat(),
                "status": evidence.integrity_status
            }
            if evidence.chain_of_custody_log:
                new_log = list(evidence.chain_of_custody_log)
                new_log.append(log_entry)
                evidence.chain_of_custody_log = new_log
            else:
                evidence.chain_of_custody_log = [log_entry]
                
            self.db.commit()

        return is_intact
