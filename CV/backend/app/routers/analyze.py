from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
import json
import os
from typing import List

from app.schemas import JobProfileCreate, CandidateResult, AnalyzeResponse, CandidateActionRequest, JobProfile
from app.config import settings
from app.services.parsing import extract_text_from_file
from app.services.chains_enhanced import run_enhanced_pipeline
from app.services.exports import export_to_csv, export_to_pdf

router = APIRouter()

@router.post("/{role_id}", response_model=AnalyzeResponse)
async def analyze_role(role_id: str):
    """Analyze new uploaded CVs for a role (incremental analysis)"""
    try:
        # Load role data
        role_file = os.path.join(settings.ROLES_DIR, f"{role_id}.json")
        if not os.path.exists(role_file):
            raise HTTPException(status_code=404, detail="Role not found")
        
        with open(role_file, 'r') as f:
            role_data = json.load(f)
        
        job_profile = JobProfile(**role_data)
        
        # Get uploaded files
        upload_dir = os.path.join(settings.UPLOADS_DIR, role_id)
        if not os.path.exists(upload_dir):
            raise HTTPException(status_code=404, detail="No files uploaded for this role")
        
        # Load existing results if they exist
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        existing_results = []
        analyzed_candidates = set()
        
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                existing_data = json.load(f)
                existing_results = [CandidateResult(**result) for result in existing_data.get("results", [])]
                analyzed_candidates = {result.candidate_id for result in existing_results}
        
        # Only analyze new files that haven't been processed yet
        new_results = []
        
        for filename in os.listdir(upload_dir):
            if '_' in filename:
                candidate_id = filename.split('_')[0]
                original_name = '_'.join(filename.split('_')[1:])
                
                # Skip if already analyzed
                if candidate_id in analyzed_candidates:
                    continue
                
                file_path = os.path.join(upload_dir, filename)
                
                try:
                    # Extract text from CV
                    cv_text = extract_text_from_file(file_path)
                    
                    # Run AI analysis pipeline
                    result = await run_enhanced_pipeline(cv_text, job_profile, candidate_id, original_name)
                    new_results.append(result)
                    
                except Exception as e:
                    # Create error result for failed files
                    error_result = CandidateResult(
                        candidate_id=candidate_id,
                        file_name=original_name,
                        fit_score=0.0,
                        why=[f"Analysis failed: {str(e)}"],
                        cv_summary="Unable to analyze this CV due to parsing or processing errors.",
                        suggested_roles=["Unknown"],
                        red_flags=["File processing error"]
                    )
                    new_results.append(error_result)
        
        # Combine existing and new results
        all_results = existing_results + new_results
        
        # Sort by fit_score descending
        all_results.sort(key=lambda x: x.fit_score, reverse=True)
        
        # Save updated results
        analysis_response = AnalyzeResponse(role_id=role_id, results=all_results)
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        
        with open(results_file, 'w') as f:
            json.dump(analysis_response.dict(), f, indent=2, default=str)
        
        return analysis_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{role_id}/results", response_model=AnalyzeResponse)
async def get_results(role_id: str):
    """Get analysis results for a role"""
    try:
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        
        if not os.path.exists(results_file):
            raise HTTPException(status_code=404, detail="No analysis results found")
        
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        return AnalyzeResponse(**results_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@router.get("/{role_id}/export/csv")
async def export_csv(role_id: str):
    """Export results as CSV"""
    try:
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        
        if not os.path.exists(results_file):
            raise HTTPException(status_code=404, detail="No analysis results found")
        
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        results = AnalyzeResponse(**results_data)
        csv_content = export_to_csv(results)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analysis_{role_id}.csv"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")

@router.get("/{role_id}/export/pdf")
async def export_pdf(role_id: str):
    """Export results as PDF"""
    try:
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        
        if not os.path.exists(results_file):
            raise HTTPException(status_code=404, detail="No analysis results found")
        
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        results = AnalyzeResponse(**results_data)
        
        # Load role data for PDF header
        role_file = os.path.join(settings.ROLES_DIR, f"{role_id}.json")
        with open(role_file, 'r') as f:
            role_data = json.load(f)
        
        job_profile = JobProfile(**role_data)
        
        pdf_path = export_to_pdf(results, job_profile, role_id)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"analysis_{role_id}.pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@router.post("/{role_id}/candidate-action")
async def update_candidate_status(role_id: str, action_request: CandidateActionRequest):
    """Update candidate status (favorite/delete)"""
    try:
        # Load existing results
        results_file = os.path.join(settings.RESULTS_DIR, f"{role_id}.json")
        
        if not os.path.exists(results_file):
            raise HTTPException(status_code=404, detail="No analysis results found")
        
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        # Find and update the candidate
        updated = False
        for result in results_data["results"]:
            if result["candidate_id"] == action_request.candidate_id:
                if action_request.action == "favorite":
                    result["is_favorite"] = True
                elif action_request.action == "unfavorite":
                    result["is_favorite"] = False
                elif action_request.action == "delete":
                    result["is_deleted"] = True
                elif action_request.action == "restore":
                    result["is_deleted"] = False
                updated = True
                break
        
        if not updated:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Save updated results
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        return {"status": "success", "message": f"Candidate {action_request.action} successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")
