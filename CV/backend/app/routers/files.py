from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import uuid
import shutil

from app.schemas import UploadResponse
from app.config import settings

router = APIRouter()

@router.post("/{role_id}", response_model=List[UploadResponse])
async def upload_files(role_id: str, files: List[UploadFile] = File(...)):
    """Upload CV files for a role"""
    try:
        # Check if role exists
        role_file = os.path.join(settings.ROLES_DIR, f"{role_id}.json")
        if not os.path.exists(role_file):
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Create uploads directory for this role
        upload_dir = os.path.join(settings.UPLOADS_DIR, role_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            # Validate file type
            if not file.filename:
                continue
                
            file_extension = file.filename.lower().split('.')[-1]
            if file_extension not in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_extension}. Supported types: PDF, DOC, DOCX, TXT, RTF, ODT"
                )
            
            # Generate unique candidate ID
            candidate_id = str(uuid.uuid4())
            
            # Save file with candidate ID prefix
            file_path = os.path.join(upload_dir, f"{candidate_id}_{file.filename}")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append(UploadResponse(
                candidate_id=candidate_id,
                file_name=file.filename,
                status="uploaded"
            ))
        
        return uploaded_files
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{role_id}/files")
async def list_uploaded_files(role_id: str):
    """List uploaded files for a role"""
    try:
        upload_dir = os.path.join(settings.UPLOADS_DIR, role_id)
        
        if not os.path.exists(upload_dir):
            return []
        
        files = []
        for filename in os.listdir(upload_dir):
            if '_' in filename:
                candidate_id = filename.split('_')[0]
                original_name = '_'.join(filename.split('_')[1:])
                files.append({
                    "candidate_id": candidate_id,
                    "file_name": original_name,
                    "status": "uploaded"
                })
        
        return files
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")
