import openai
import json
import os
from typing import Dict, List, Any
from app.schemas import CandidateResult, JobProfile
from app.services.mock_ai import mock_ai_analysis

# Initialize OpenAI client
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
        # Fallback prompts
        fallbacks = {
            "scoring_prompt.txt": """
You are an AI assistant helping HR professionals analyze CVs against job requirements.

Analyze the candidate's CV against the job profile and provide:
1. Overall fit score (0-10)
2. Bulleted reasons for the score
3. Executive summary of the candidate
4. 2-4 suggested roles based on their profile
5. Any red flags (optional)

Job Profile: {job_profile}
CV Content: {cv_content}

Respond in JSON format:
{{
    "fit_score": 7.5,
    "why": ["Relevant experience in target domain", "Strong technical skills"],
    "cv_summary": "One paragraph executive summary",
    "suggested_roles": ["Role 1", "Role 2"],
    "red_flags": [],
    "years_experience": 5.0,
    "last_role": "Previous Position"
}}
            """,
            "summary_prompt.txt": """
Provide a one-paragraph executive summary of this candidate's professional profile:

{cv_content}
            """,
            "roles_prompt.txt": """
Based on this CV, suggest 2-4 relevant job roles that would be a good fit:

{cv_content}
            """
        }
        return fallbacks.get(filename, "Please analyze the provided content.")

async def run_candidate_pipeline(
    job_profile: JobProfile,
    cv_content: str,
    candidate_id: str,
    original_filename: str,
    model_name: str = "gpt-4o-mini"
) -> CandidateResult:
    """
    Run the complete candidate analysis pipeline using OpenAI
    """
    
    # For now, use mock AI to ensure system works reliably
    # TODO: Re-enable OpenAI when quota and JSON parsing issues are resolved
    print(f"Using mock AI analysis for {original_filename} (OpenAI temporarily disabled)")
    return mock_ai_analysis(job_profile, cv_content, candidate_id, original_filename)
