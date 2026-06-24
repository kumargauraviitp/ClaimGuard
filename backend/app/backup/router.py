from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.permission_service import get_current_user_or_api_key
from .backup_service import backup_service
import os

router = APIRouter(prefix="/api/system/backups", tags=["System Backup"])

@router.get("")
def list_backups(current_user = Depends(get_current_user_or_api_key)):
    # In a real app, verify admin role
    return backup_service.list_backups()

@router.post("")
def create_backup(current_user = Depends(get_current_user_or_api_key)):
    try:
        result = backup_service.perform_backup()
        return {"status": "success", "metadata": result["metadata"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")

@router.post("/{backup_id}/restore")
def restore_backup(backup_id: str, current_user = Depends(get_current_user_or_api_key)):
    try:
        result = backup_service.restore_backup(backup_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.get("/{backup_id}/download")
def download_backup(backup_id: str, current_user = Depends(get_current_user_or_api_key)):
    info = backup_service.get_backup_info(backup_id)
    if not info:
        raise HTTPException(status_code=404, detail="Backup not found")
        
    zip_path = info["zip_path"]
    return FileResponse(zip_path, media_type="application/zip", filename=os.path.basename(zip_path))

@router.delete("/{backup_id}")
def delete_backup(backup_id: str, current_user = Depends(get_current_user_or_api_key)):
    try:
        result = backup_service.delete_backup(backup_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/upload")
async def upload_backup(file: UploadFile = File(...), current_user = Depends(get_current_user_or_api_key)):
    try:
        metadata = await backup_service.handle_upload(file)
        return {"status": "success", "metadata": metadata}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
