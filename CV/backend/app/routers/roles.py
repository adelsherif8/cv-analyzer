from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
import uuid
from datetime import datetime

from app.schemas import JobProfileCreate, JobProfile, DeleteRequest
from app.config import settings
from app.services.skill_suggestions import suggest_skills_for_role

router = APIRouter()

@router.post("/", response_model=JobProfile)
async def create_role(role_data: JobProfileCreate):
    """Create a new job profile"""
    try:
        # Generate unique ID
        role_id = str(uuid.uuid4())
        
        # Create job profile
        job_profile = JobProfile(
            id=role_id,
            title=role_data.title,
            description=role_data.description,
            required_skills=role_data.required_skills,
            created_at=datetime.now()
        )
        
        # Save to file
        role_file = os.path.join(settings.ROLES_DIR, f"{role_id}.json")
        with open(role_file, 'w') as f:
            json.dump(job_profile.dict(), f, indent=2, default=str)
        
        return job_profile
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")

@router.get("/{role_id}", response_model=JobProfile)
async def get_role(role_id: str):
    """Get a job profile by ID"""
    try:
        role_file = os.path.join(settings.ROLES_DIR, f"{role_id}.json")
        
        if not os.path.exists(role_file):
            raise HTTPException(status_code=404, detail="Role not found")
        
        with open(role_file, 'r') as f:
            role_data = json.load(f)
        
        return JobProfile(**role_data)
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Role not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get role: {str(e)}")

@router.delete("/{role_id}")
async def delete_role(role_id: str):
    """Delete a job profile and all associated data"""
    try:
        # Delete role file
        role_file = os.path.join(settings.ROLES_DIR, f"{role_id}.json")
        if os.path.exists(role_file):
            os.remove(role_file)
        
        # Delete uploads directory
        uploads_dir = os.path.join(settings.UPLOADS_DIR, role_id)
        if os.path.exists(uploads_dir):
            import shutil
            shutil.rmtree(uploads_dir)
        
        # Delete results file
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        if os.path.exists(results_file):
            os.remove(results_file)
        
        return {"message": "Role and associated data deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete role: {str(e)}")

@router.get("/", response_model=List[JobProfile])
async def list_roles():
    """List all job profiles"""
    try:
        roles = []
        roles_dir = settings.ROLES_DIR
        
        if os.path.exists(roles_dir):
            for filename in os.listdir(roles_dir):
                if filename.endswith('.json'):
                    role_file = os.path.join(roles_dir, filename)
                    with open(role_file, 'r') as f:
                        role_data = json.load(f)
                    roles.append(JobProfile(**role_data))
        
        return roles
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list roles: {str(e)}")

@router.post("/suggest-skills")
async def get_skill_suggestions(request: dict):
    """Get skill suggestions based on job title and description"""
    try:
        title = request.get("title", "")
        description = request.get("description", "")
        
        if not title and not description:
            raise HTTPException(status_code=400, detail="Either title or description is required")
        
        suggestions = suggest_skills_for_role(title, description)
        return suggestions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate skill suggestions: {str(e)}")
