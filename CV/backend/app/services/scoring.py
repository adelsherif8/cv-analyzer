import re
from typing import List, Dict, Any
import json

from app.schemas import CandidateResult, JobProfile, SkillMatch, ScoringResult

def calculate_skill_score(required_skill: Dict[str, Any], skill_matches: List[SkillMatch]) -> float:
    """Calculate score for a single required skill"""
    skill_name = required_skill["name"]
    skill_weight = required_skill["weight"]
    
    # Find matching skill from LLM analysis
    skill_match = None
    for match in skill_matches:
        if match.name.lower() == skill_name.lower():
            skill_match = match
            break
    
    if not skill_match:
        return 0.0
    
    # Use LLM match score as base
    base_score = skill_match.match
    
    # Apply weight
    weighted_score = base_score * skill_weight
    
    return weighted_score

def calculate_experience_score(experience_years: float) -> float:
    """Calculate experience score based on years (0-1 scale)"""
    if experience_years <= 0:
        return 0.0
    elif experience_years >= 10:
        return 1.0
    else:
        return experience_years / 10.0

def calculate_project_evidence_boost(project_evidence: List[str], cv_text: str) -> float:
    """Calculate project evidence boost"""
    if not project_evidence:
        return 0.0
    
    # Check for portfolio/GitHub links
    portfolio_patterns = [
        r'github\.com',
        r'gitlab\.com',
        r'portfolio',
        r'projects?',
        r'demo',
        r'live\s+site'
    ]
    
    cv_lower = cv_text.lower()
    has_portfolio = any(re.search(pattern, cv_lower) for pattern in portfolio_patterns)
    
    # Check for Shopify-specific evidence
    shopify_patterns = [
        r'shopify',
        r'liquid',
        r'theme',
        r'storefront',
        r'e-commerce',
        r'ecommerce'
    ]
    
    has_shopify = any(re.search(pattern, cv_lower) for pattern in shopify_patterns)
    
    # Base boost from project evidence
    base_boost = min(len(project_evidence) * 0.1, 0.3)
    
    # Additional boosts
    portfolio_boost = 0.1 if has_portfolio else 0.0
    shopify_boost = 0.1 if has_shopify else 0.0
    
    total_boost = base_boost + portfolio_boost + shopify_boost
    return min(total_boost, 0.5)  # Cap at 0.5

def calculate_fit_score(
    job_profile: JobProfile,
    scoring_result: ScoringResult,
    cv_text: str
) -> float:
    """Calculate overall fit score (0-10)"""
    
    # Calculate weighted skill scores
    total_skill_score = 0.0
    total_weight = 0.0
    
    for required_skill in job_profile.required_skills:
        skill_score = calculate_skill_score(required_skill.dict(), scoring_result.skill_matches)
        total_skill_score += skill_score
        total_weight += required_skill.weight
    
    # Normalize by total weight
    if total_weight > 0:
        normalized_skill_score = total_skill_score / total_weight
    else:
        normalized_skill_score = 0.0
    
    # Calculate experience component
    experience_score = calculate_experience_score(scoring_result.experience_years)
    
    # Calculate project evidence boost
    evidence_boost = calculate_project_evidence_boost(scoring_result.project_evidence, cv_text)
    
    # Combine scores
    # Skills: 70%, Experience: 20%, Evidence boost: up to 10%
    base_score = (normalized_skill_score * 0.7) + (experience_score * 0.2)
    
    # Apply evidence boost
    final_score = base_score + evidence_boost
    
    # Scale to 0-10 and clamp
    final_score = min(max(final_score * 8.5, 0.0), 10.0)
    
    return round(final_score, 1)

def generate_why_rationale(
    job_profile: JobProfile,
    scoring_result: ScoringResult,
    fit_score: float
) -> List[str]:
    """Generate bulleted rationale for the fit score"""
    rationale = []
    
    # Skill matches
    strong_skills = [match for match in scoring_result.skill_matches if match.match >= 0.7]
    if strong_skills:
        skill_names = [skill.name for skill in strong_skills[:3]]
        rationale.append(f"Strong match for key skills: {', '.join(skill_names)}")
    
    weak_skills = [match for match in scoring_result.skill_matches if match.match < 0.5]
    if weak_skills:
        skill_names = [skill.name for skill in weak_skills[:2]]
        rationale.append(f"Limited experience in: {', '.join(skill_names)}")
    
    # Experience
    if scoring_result.experience_years >= 5:
        rationale.append(f"Solid experience ({scoring_result.experience_years} years)")
    elif scoring_result.experience_years >= 2:
        rationale.append(f"Moderate experience ({scoring_result.experience_years} years)")
    else:
        rationale.append("Junior level experience")
    
    # Project evidence
    if scoring_result.project_evidence:
        evidence_count = len(scoring_result.project_evidence)
        rationale.append(f"Demonstrated impact with {evidence_count} quantified achievements")
    
    # Overall assessment
    if fit_score >= 8.0:
        rationale.append("Excellent overall fit for this role")
    elif fit_score >= 6.0:
        rationale.append("Good fit with some skill gaps to address")
    elif fit_score >= 4.0:
        rationale.append("Moderate fit, would need significant development")
    else:
        rationale.append("Limited fit for this specific role")
    
    return rationale

def extract_last_role(cv_text: str) -> str:
    """Extract the most recent job title from CV text"""
    # Simple pattern matching for job titles
    title_patterns = [
        r'(?:current|present|recent)\s+(?:role|position|title):\s*([^\n\.]+)',
        r'(?:software|web|frontend|backend|full\s*stack|developer|engineer|architect)\s*(?:developer|engineer)?',
        r'(?:senior|lead|principal|junior)\s+(?:developer|engineer|analyst|consultant)',
        r'(?:manager|director|lead)\s+(?:of\s+)?(?:engineering|development|technology)'
    ]
    
    cv_lower = cv_text.lower()
    
    for pattern in title_patterns:
        matches = re.findall(pattern, cv_lower)
        if matches:
            # Return the first match, cleaned up
            title = matches[0].strip().title()
            return title[:50]  # Limit length
    
    return "Unknown"

def extract_years_experience(cv_text: str) -> float:
    """Extract years of experience from CV text"""
    patterns = [
        r'(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
        r'(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, cv_text.lower())
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                continue
    
    # Fallback: try to estimate from work history dates
    year_pattern = r'\b(19|20)\d{2}\b'
    years = re.findall(year_pattern, cv_text)
    if len(years) >= 2:
        try:
            years = [int(y) for y in years]
            years.sort()
            experience = 2024 - years[0]  # Rough estimate
            return min(experience, 20)  # Cap at 20 years
        except:
            pass
    
    return 0.0

def combine_analysis_results(
    job_profile: JobProfile,
    scoring_result: ScoringResult,
    cv_summary: str,
    suggested_roles: List[str],
    candidate_id: str,
    file_name: str,
    cv_text: str
) -> CandidateResult:
    """Combine all analysis results into final candidate result"""
    
    # Calculate fit score
    fit_score = calculate_fit_score(job_profile, scoring_result, cv_text)
    
    # Generate rationale
    why = generate_why_rationale(job_profile, scoring_result, fit_score)
    
    # Extract additional info
    last_role = extract_last_role(cv_text)
    years_experience = extract_years_experience(cv_text)
    
    return CandidateResult(
        candidate_id=candidate_id,
        file_name=file_name,
        fit_score=fit_score,
        why=why,
        cv_summary=cv_summary,
        suggested_roles=suggested_roles,
        red_flags=scoring_result.red_flags if scoring_result.red_flags else None,
        years_experience=years_experience,
        last_role=last_role
    )
