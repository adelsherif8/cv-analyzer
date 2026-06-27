"""
Enhanced CV Analysis Pipeline using the CV Analyzer Agent

Integrates the full specification CV analyzer with OpenAI for hybrid analysis
"""

import openai
import json
import os
import re
from typing import Dict, List, Any, Optional
from app.schemas import CandidateResult, JobProfile, CandidateDetails, SkillAnalysis
from app.services.cv_analyzer_agent import cv_analyzer
from app.services.rag import CVRetriever
import logging

logger = logging.getLogger(__name__)

def get_openai_client():
    """Get OpenAI client with API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return openai.OpenAI(api_key=api_key)

def load_prompt(filename: str) -> str:
    """Load prompt from file with fallback"""
    try:
        prompt_path = os.path.join("app", "prompts", filename)
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Prompt file {filename} not found, using fallback")
        return ""

async def run_enhanced_pipeline(
    cv_content: str,
    job_profile: JobProfile,
    candidate_id: str = "unknown",
    file_name: str = "unknown.pdf",
    model_name: str = "gpt-4o-mini"
) -> CandidateResult:
    """
    Run the enhanced candidate analysis pipeline
    
    Uses the CV Analyzer Agent for deterministic scoring following the specification,
    then enhances with OpenAI for narrative generation and details extraction.
    """
    
    try:
        # Step 1: Run the deterministic CV analyzer agent
        logger.info(f"Running CV analyzer agent for candidate {candidate_id}")
        analysis_result = cv_analyzer.analyze_candidate(
            cv_content,
            job_profile,
            candidate_id
        )

        # Step 1b: RAG — index the CV and retrieve the passages most relevant to
        # the job requirements. These ground the summary instead of a blind truncation.
        retriever = CVRetriever().build(cv_content)
        rag_query = f"{job_profile.title}. Required skills: " + ", ".join(
            s.name for s in job_profile.required_skills
        )
        retrieved = retriever.retrieve(rag_query, k=4)
        retrieved_passages = [chunk for chunk, _score in retrieved]
        logger.info(
            f"RAG: retrieved {len(retrieved_passages)} passages via {retriever.mode}"
        )

        # Step 2: Extract additional candidate details using OpenAI
        candidate_details = await extract_candidate_details_with_ai(cv_content, model_name)

        # Step 3: Generate enhanced narrative summary using OpenAI, grounded on RAG passages
        cv_summary = await generate_enhanced_summary(
            cv_content, analysis_result, model_name, retrieved_passages
        )
        
        # Step 4: Generate markdown narrative
        markdown_narrative = cv_analyzer.generate_narrative_output(analysis_result, cv_content)
        
        # Step 5: Create skill analysis dict for backward compatibility
        skill_analysis = {}
        for rating in analysis_result.ratings:
            skill_analysis[rating.skill] = SkillAnalysis(
                score=rating.rating,
                evidence=rating.evidence,
                years_experience=analysis_result.candidate.years_experience
            )
        
        # Step 6: Create final CandidateResult
        result = CandidateResult(
            candidate_id=candidate_id,
            file_name=file_name,
            fit_score=analysis_result.weighted_score.score_10,
            why=[f"Score: {analysis_result.weighted_score.score_10}/10 ({analysis_result.weighted_score.match_pct}% match)"] + 
                [f"{r.skill}: {r.rating}/10" for r in analysis_result.ratings[:3]],
            cv_summary=cv_summary,
            suggested_roles=analysis_result.best_role_fit,
            red_flags=analysis_result.red_flags,
            years_experience=analysis_result.candidate.years_experience,
            last_role=extract_last_role_from_cv(cv_content),
            candidate_details=candidate_details,
            skill_analysis=skill_analysis,
            full_analysis=analysis_result,  # Include complete analysis
            retrieved_context=retrieved_passages,
            retrieval_mode=retriever.mode,
        )

        return result
        
    except Exception as e:
        logger.error(f"Error in enhanced pipeline: {str(e)}")
        
        # Fallback to basic analysis
        return await fallback_analysis(
            cv_content, job_profile, candidate_id, file_name, model_name
        )

async def extract_candidate_details_with_ai(cv_content: str, model_name: str) -> Optional[CandidateDetails]:
    """Extract candidate contact details using OpenAI"""
    try:
        client = get_openai_client()
        
        prompt = f"""
Extract contact information from this CV and return as JSON:

{cv_content[:2000]}

Return only JSON in this format:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "location": "City, Country",
    "linkedin": "linkedin.com/in/profile",
    "github": "github.com/username",
    "portfolio": "portfolio-url.com",
    "other_links": ["url1", "url2"]
}}

If any field is not found, use null.
"""
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Extract contact information and return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        
        # Try to parse JSON
        try:
            details_data = json.loads(result_text)
            return CandidateDetails(**details_data)
        except json.JSONDecodeError:
            logger.warning("Failed to parse candidate details JSON")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting candidate details: {str(e)}")
        return None

async def generate_enhanced_summary(cv_content: str, analysis_result, model_name: str,
                                    retrieved_passages: Optional[List[str]] = None) -> str:
    """Generate enhanced CV summary using OpenAI, grounded on RAG-retrieved passages."""
    try:
        client = get_openai_client()

        # Create context from analysis
        context = f"""
Candidate Analysis Summary:
- Experience: {analysis_result.candidate.years_experience:.1f} years
- Overall Score: {analysis_result.weighted_score.score_10}/10 ({analysis_result.weighted_score.match_pct}% match)
- Top Skills: {', '.join([r.skill for r in analysis_result.ratings[:3] if r.rating >= 6.0])}
- Fit Assessment: {analysis_result.fit_assessment.label}
"""

        # RAG: prefer retrieved passages (most relevant to the role) over a blind
        # truncation of the CV. Fall back to the first 1500 chars if retrieval is empty.
        if retrieved_passages:
            cv_context = "\n".join(f"- {p}" for p in retrieved_passages)
            cv_context_label = "Retrieved CV passages (most relevant to the role)"
        else:
            cv_context = cv_content[:1500]
            cv_context_label = "CV Content (first 1500 chars)"

        prompt = f"""
Write a concise 2-3 sentence executive summary for this candidate based on their CV and analysis:

{context}

{cv_context_label}:
{cv_context}

Focus on:
- Professional background and experience level
- Key strengths and expertise areas
- Overall fit for the role

Ground every claim in the retrieved passages above. Keep it professional, factual, and recruiter-friendly.
"""
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an executive recruiter writing candidate summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating enhanced summary: {str(e)}")
        return f"Professional candidate with {analysis_result.candidate.years_experience:.1f} years of experience in the target domain."

def extract_last_role_from_cv(cv_content: str) -> str:
    """Extract the most recent job title from CV"""
    lines = cv_content.split('\n')
    
    # Look for patterns that indicate job titles
    title_patterns = [
        r'^([^,\n]{10,50})\s*(?:at|@|\s-\s)',  # Title at Company
        r'^([A-Z][^,\n]{5,40})\s*\n',  # Capitalized title on its own line
    ]
    
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        if not line or len(line) < 5:
            continue
            
        for pattern in title_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Filter out obvious non-titles
                if not any(skip in title.lower() for skip in ['experience', 'summary', 'objective', 'email', 'phone']):
                    return title
    
    return "Professional"

async def fallback_analysis(cv_content: str, job_profile: JobProfile, 
                          candidate_id: str, file_name: str, model_name: str) -> CandidateResult:
    """Fallback analysis when main pipeline fails"""
    logger.info("Running fallback analysis")
    
    try:
        # Simple OpenAI analysis
        client = get_openai_client()
        
        prompt = f"""
Analyze this CV against the job requirements and return JSON:

Job: {job_profile.title}
Required Skills: {', '.join([s.name for s in job_profile.required_skills])}

CV: {cv_content[:2000]}

Return JSON:
{{
    "fit_score": 7.0,
    "why": ["reason1", "reason2"],
    "cv_summary": "summary",
    "suggested_roles": ["role1", "role2"],
    "red_flags": [],
    "years_experience": 5.0
}}
"""
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an HR analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        result_text = response.choices[0].message.content
        result_data = json.loads(result_text)
        
        return CandidateResult(
            candidate_id=candidate_id,
            file_name=file_name,
            fit_score=result_data.get("fit_score", 5.0),
            why=result_data.get("why", ["Analysis completed"]),
            cv_summary=result_data.get("cv_summary", "Professional candidate"),
            suggested_roles=result_data.get("suggested_roles", ["General Role"]),
            red_flags=result_data.get("red_flags", []),
            years_experience=result_data.get("years_experience", 0.0),
            last_role="Professional"
        )
        
    except Exception as e:
        logger.error(f"Fallback analysis failed: {str(e)}")
        
        # Ultimate fallback
        return CandidateResult(
            candidate_id=candidate_id,
            file_name=file_name,
            fit_score=5.0,
            why=["Analysis completed with limited data"],
            cv_summary="Professional candidate profile analyzed",
            suggested_roles=["General Position"],
            red_flags=[],
            years_experience=0.0,
            last_role="Professional"
        )

# Maintain backward compatibility
async def run_candidate_pipeline(
    cv_content: str,
    job_profile: JobProfile,
    model_name: str = "gpt-4o-mini"
) -> CandidateResult:
    """
    Backward compatible wrapper for the enhanced pipeline
    """
    return await run_enhanced_pipeline(
        cv_content=cv_content,
        job_profile=job_profile,
        candidate_id="unknown",
        file_name="unknown.pdf",
        model_name=model_name
    )
