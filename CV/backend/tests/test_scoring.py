import pytest
from app.services.scoring import calculate_skill_score, calculate_experience_score, calculate_fit_score
from app.schemas import SkillMatch, ScoringResult, JobProfile, SkillWeight

def test_calculate_skill_score():
    """Test skill score calculation"""
    required_skill = {"name": "React", "weight": 0.5}
    skill_matches = [
        SkillMatch(name="React", match=0.8, evidence=["3 years experience"])
    ]
    
    score = calculate_skill_score(required_skill, skill_matches)
    assert score == 0.4  # 0.8 * 0.5

def test_calculate_experience_score():
    """Test experience score calculation"""
    assert calculate_experience_score(0) == 0.0
    assert calculate_experience_score(5) == 0.5
    assert calculate_experience_score(10) == 1.0
    assert calculate_experience_score(15) == 1.0  # Capped at 1.0

def test_fit_score_calculation():
    """Test overall fit score calculation"""
    job_profile = JobProfile(
        id="test",
        title="Test Role",
        description="Test description",
        required_skills=[
            SkillWeight(name="React", weight=0.6),
            SkillWeight(name="JavaScript", weight=0.4)
        ]
    )
    
    scoring_result = ScoringResult(
        skill_matches=[
            SkillMatch(name="React", match=0.8, evidence=["Strong React skills"]),
            SkillMatch(name="JavaScript", match=0.9, evidence=["Expert JS"])
        ],
        experience_years=5.0,
        project_evidence=["Built 3 projects"],
        red_flags=[]
    )
    
    cv_text = "Sample CV text with React and JavaScript experience"
    
    fit_score = calculate_fit_score(job_profile, scoring_result, cv_text)
    
    # Score should be between 0 and 10
    assert 0 <= fit_score <= 10
    assert isinstance(fit_score, float)

def test_clamp_function():
    """Test that scores are properly clamped"""
    # Test with very high input that should be clamped
    job_profile = JobProfile(
        id="test",
        title="Test Role", 
        description="Test description",
        required_skills=[SkillWeight(name="React", weight=1.0)]
    )
    
    scoring_result = ScoringResult(
        skill_matches=[SkillMatch(name="React", match=1.0, evidence=["Perfect match"])],
        experience_years=20.0,  # Very high experience
        project_evidence=["Many projects"] * 10,  # Lots of evidence
        red_flags=[]
    )
    
    cv_text = "CV with React, GitHub, portfolio, Shopify, liquid, theme development"
    
    fit_score = calculate_fit_score(job_profile, scoring_result, cv_text)
    
    # Should be clamped at 10.0
    assert fit_score <= 10.0

def test_weight_math():
    """Test that weights are properly applied"""
    # High weight skill with low match should impact score more than low weight skill with high match
    job_profile = JobProfile(
        id="test",
        title="Test Role",
        description="Test description", 
        required_skills=[
            SkillWeight(name="CriticalSkill", weight=0.8),
            SkillWeight(name="MinorSkill", weight=0.2)
        ]
    )
    
    # Scenario 1: Strong in critical skill, weak in minor skill
    scoring_result_1 = ScoringResult(
        skill_matches=[
            SkillMatch(name="CriticalSkill", match=0.9, evidence=["Strong"]),
            SkillMatch(name="MinorSkill", match=0.1, evidence=["Weak"])
        ],
        experience_years=3.0,
        project_evidence=[],
        red_flags=[]
    )
    
    # Scenario 2: Weak in critical skill, strong in minor skill  
    scoring_result_2 = ScoringResult(
        skill_matches=[
            SkillMatch(name="CriticalSkill", match=0.1, evidence=["Weak"]),
            SkillMatch(name="MinorSkill", match=0.9, evidence=["Strong"])
        ],
        experience_years=3.0,
        project_evidence=[],
        red_flags=[]
    )
    
    cv_text = "Sample CV text"
    
    score_1 = calculate_fit_score(job_profile, scoring_result_1, cv_text)
    score_2 = calculate_fit_score(job_profile, scoring_result_2, cv_text)
    
    # Candidate 1 should score higher due to better performance on higher-weighted skill
    assert score_1 > score_2

if __name__ == "__main__":
    pytest.main([__file__])
