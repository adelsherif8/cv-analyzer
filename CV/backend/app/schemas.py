from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Literal
from datetime import datetime

class SkillWeight(BaseModel):
    name: str
    weight: float = Field(ge=0, le=1, description="Weight for this skill (0-1)")
    critical: bool = Field(default=False, description="Whether this is a critical skill")
    is_bonus: bool = Field(default=False, description="Whether this is a bonus skill")
    category: str = Field(default="General", description="Skill category")

class ExperienceEntry(BaseModel):
    title: str
    company: str
    start: str
    end: Optional[str] = None
    current: bool = False
    bullets: List[str] = Field(default=[], description="Achievement bullets")
    tech: List[str] = Field(default=[], description="Technologies used")

class CandidateCV(BaseModel):
    raw_text: str
    sections: Optional[Dict] = Field(default=None, description="Parsed CV sections")

class JobProfileCreate(BaseModel):
    title: str = Field(description="Job title")
    description: str = Field(description="Job description")
    required_skills: List[SkillWeight] = Field(description="Required skills with weights")
    seniority: Literal["junior", "mid", "senior"] = Field(default="mid", description="Required seniority level")
    nice_to_have: List[str] = Field(default=[], description="Nice to have skills")
    must_have_keywords: List[str] = Field(default=[], description="Must have keywords")
    locale: str = Field(default="en", description="Job locale")

class JobProfile(JobProfileCreate):
    id: str = Field(description="Unique job profile ID")
    created_at: datetime = Field(default_factory=datetime.now)

class SkillAdjustments(BaseModel):
    recency_factor: float = Field(description="Recency adjustment factor")
    tenure_factor: float = Field(description="Tenure adjustment factor")
    scope_bonus: float = Field(default=0.0, description="Scope/impact bonus")
    seniority_penalty: float = Field(default=0.0, description="Seniority mismatch penalty")

class SkillRating(BaseModel):
    skill: str
    weight: float
    critical: bool
    rating: float = Field(ge=0, le=10, description="Final adjusted rating (0-10)")
    evidence_confidence: Literal["E1", "E2", "E3"] = Field(description="Evidence confidence level")
    evidence: List[str] = Field(description="Supporting evidence from CV")
    adjustments: SkillAdjustments
    reason: str = Field(default="", description="Reason for score (e.g., weak evidence, stale usage)")

class WeightedScore(BaseModel):
    score_10: float = Field(description="Final score out of 10")
    match_pct: int = Field(description="Match percentage")

class FitAssessment(BaseModel):
    label: Literal["good", "partial", "poor"]
    reason: str

class ATSKeywords(BaseModel):
    found: List[str]
    missing: List[str]

class CandidateAnalysis(BaseModel):
    name: Optional[str] = None
    years_experience: float
    locale: str

class AnalysisResult(BaseModel):
    candidate: CandidateAnalysis
    job_profile: Dict
    ratings: List[SkillRating]
    weighted_score: WeightedScore
    highlights: List[str]
    pros: List[str]
    cons: List[str]
    ats_keywords: ATSKeywords
    growth_plan: List[str]
    fit_assessment: FitAssessment
    best_role_fit: List[str]
    red_flags: List[str] = Field(default=[])

class UploadResponse(BaseModel):
    candidate_id: str
    file_name: str
    status: str = "uploaded"

class SkillMatch(BaseModel):
    name: str
    match: float = Field(ge=0, le=1)
    evidence: List[str]

class ScoringResult(BaseModel):
    skill_matches: List[SkillMatch]
    experience_years: float
    project_evidence: List[str]
    red_flags: List[str] = []

class CandidateDetails(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other_links: List[str] = Field(default=[], description="Additional websites or links")

class SkillAnalysis(BaseModel):
    score: float = Field(ge=0, le=10, description="Skill score (0-10)")
    evidence: List[str] = Field(description="Evidence from CV")
    years_experience: Optional[float] = None

class CandidateResult(BaseModel):
    candidate_id: str
    file_name: str
    fit_score: float = Field(ge=0, le=10, description="Overall fit score (0-10)")
    why: List[str] = Field(description="Bulleted rationale for the score")
    cv_summary: str = Field(description="One paragraph executive summary")
    suggested_roles: List[str] = Field(description="2-4 suggested roles")
    red_flags: List[str] = Field(default=[], description="Potential concerns")
    years_experience: Optional[float] = None
    last_role: Optional[str] = None
    candidate_details: Optional[CandidateDetails] = None
    is_favorite: bool = Field(default=False, description="Marked as favorite")
    is_deleted: bool = Field(default=False, description="Marked as deleted")
    skill_analysis: Optional[Dict[str, SkillAnalysis]] = Field(default=None, description="Detailed skill analysis")
    # Add new field for full analysis result
    full_analysis: Optional[AnalysisResult] = Field(default=None, description="Complete analysis per specification")
    # RAG: the CV passages retrieved to ground the summary (semantic or TF-IDF)
    retrieved_context: Optional[List[str]] = Field(default=None, description="Top CV passages retrieved for the job (RAG evidence)")
    retrieval_mode: Optional[str] = Field(default=None, description="Retrieval backend used: embeddings | tfidf | none")

class AnalyzeResponse(BaseModel):
    role_id: str
    results: List[CandidateResult]
    analyzed_at: datetime = Field(default_factory=datetime.now)

class CandidateActionRequest(BaseModel):
    candidate_id: str
    action: str = Field(pattern="^(favorite|unfavorite|delete|restore)$")

class DeleteRequest(BaseModel):
    role_id: str

class ExportRequest(BaseModel):
    job_id: str
    format: str = Field(pattern="^(csv|pdf)$")

class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    model_name: str
