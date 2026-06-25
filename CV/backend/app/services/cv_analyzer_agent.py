"""
CV Analyzer Agent - Full Specification Implementation

Evidence-based, deterministic CV scoring system following the complete specification.
Implements:
- 10-point rating rubric with evidence confidence levels
- Recency & tenure adjustments  
- Critical skill gating
- Weight normalization
- Bias guardrails
- ATS keyword analysis
- Red fl    def calculate_scope_bonus(self, evidence: List[str]) -> float:rehensive markdown & JSON output
"""

import re
import math
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
from rapidfuzz import fuzz, process

from app.schemas import (
    JobProfile, CandidateCV, SkillRating, SkillAdjustments, 
    WeightedScore, FitAssessment, ATSKeywords, CandidateAnalysis,
    AnalysisResult, CandidateResult, CandidateDetails
)

logger = logging.getLogger(__name__)

# Section weights for evidence scoring
SECTION_WEIGHTS = {
    "experience": 1.0, "work": 1.0, "employment": 1.0, "projects": 0.9,
    "certifications": 0.5, "courses": 0.4, "education": 0.4, "summary": 0.6, "skills": 0.7
}

# Date pattern for role block detection
DATE_RE = r'((jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})|(\d{4}\s*[-–]\s*(present|\d{4}))'

# Calibration table for realistic scoring
CALIBRATION_TABLE = [(0,0),(3,3.2),(5,5.3),(7,7.2),(8.5,8.8),(10,10)]

def detect_section(line: str) -> str:
    """Detect which CV section a line belongs to"""
    l = line.lower().strip(': ')
    for k in SECTION_WEIGHTS:
        if k in l: 
            return k
    return "other"

def calibrate_score(x: float) -> float:
    """Apply calibration to make scores feel realistic"""
    for (a,b), (c,d) in zip(CALIBRATION_TABLE, CALIBRATION_TABLE[1:]):
        if a <= x <= c:
            t = (x-a)/(c-a) if c != a else 0
            return b + t*(d-b)
    return x

# Canonical skill → aliases (keywords & artifacts found in real CVs)
SKILL_ALIAS_MAP = {
    "react.js development (components, hooks, state management)": [
        "react", "reactjs", "react.js", "jsx", "react hooks", "hooks",
        "component", "components", "state management", "useState", "useEffect",
        "redux", "context api", "react router"
    ],
    "shopify & liquid templating (themes, customizations, e-commerce workflows)": [
        "shopify", "shopify (liquid)", "liquid", "liquid templating", ".liquid",
        "theme", "themes", "shopify theme", "theme customization", "sections schema",
        "snippets", "metafields", "shopify editor", "dawn", "checkout", "shopify api",
        "app embed", "cart.js", "storefront api"
    ],
    "html5, css3, and responsive design (tailwind, bootstrap, etc.)": [
        "html", "html5", "css", "css3", "responsive", "mobile-first",
        "tailwind", "bootstrap", "sass", "scss", "flexbox", "grid", "media queries"
    ],
    "javascript (es6+) & frontend best practices": [
        "javascript", "js", "es6", "es2015", "typescript", "async/await",
        "fetch", "axios", "webpack", "vite", "babel", "eslint", "prettier", "jest"
    ],
    "api integration & performance optimization": [
        "api", "rest api", "graphql", "webhooks", "integration",
        "razorpay", "stripe", "crm", "zapier", "gohighlevel",
        "lighthouse", "core web vitals", "performance", "optimization",
        "caching", "bundle size", "ttfb", "tti"
    ],
    "seo & content marketing": [
        "seo", "search engine optimization", "on-page", "technical seo", "meta tags", "schema", 
        "content briefs", "backlinks", "ga4 insights", "organic traffic", "content marketing",
        "keyword research", "google analytics", "search console"
    ],
    "paid advertising": [
        "google ads", "adwords", "search ads", "pmax", "shopping ads",
        "meta ads", "facebook ads", "instagram ads", "tiktok ads", 
        "budgets", "roas", "cpa", "bid management", "paid advertising", "ppc"
    ],
    "social media management": [
        "content calendar", "community", "sm strategy", "engagement",
        "creator mgmt", "social media management", "community management",
        "instagram", "facebook", "linkedin", "twitter", "tiktok", "social platforms"
    ],
    "email marketing": [
        "mailchimp", "klaviyo", "hubspot workflows", "segmentation",
        "automation", "flows", "drip", "ab emails", "email campaigns",
        "email marketing", "newsletters", "open rate", "click rate"
    ],
    "python": [
        "python", "django", "flask", "fastapi", "pandas", "numpy", "scikit-learn",
        "python3", "pip", "virtualenv", "jupyter", "matplotlib", "seaborn"
    ],
    "machine learning": [
        "ml", "tensorflow", "pytorch", "keras", "deep learning",
        "neural networks", "nlp", "computer vision", "data science",
        "machine learning", "ai", "artificial intelligence", "model training"
    ],
    "aws": [
        "aws", "amazon web services", "ec2", "s3", "lambda", "rds", 
        "cloudformation", "eks", "ecs", "cloudwatch", "vpc", "iam"
    ],
    "docker": [
        "docker", "containers", "kubernetes", "k8s", "containerization",
        "docker-compose", "dockerfile", "pods", "deployments"
    ],
    "leadership": [
        "team lead", "managed", "mentored", "supervised", "led team",
        "project management", "stakeholder management", "leadership",
        "team management", "people management"
    ]
}

class CVAnalyzerAgent:
    """
    CV Analyzer Agent implementing the full specification
    """
    
    def __init__(self):
        self.lambda_recency = 0.12  # Recency decay factor
        self.evidence_used = set()  # Track evidence to prevent cross-skill leakage
    
    def _sentences_with_section(self, text: str):
        """Split text into sentences with section weights"""
        s = "other"
        for raw in text.splitlines():
            if len(raw.strip()) == 0: 
                continue
            if re.match(r'^[A-Za-z].{0,40}$', raw.strip()):
                s = detect_section(raw)
            for part in re.split(r'[•\-–;.!?]', raw):
                t = part.strip()
                if len(t) > 6:
                    yield t, SECTION_WEIGHTS.get(s, 0.6)
    
    def _is_skill_dump(self, s: str) -> bool:
        """Check if sentence is a generic skills list"""
        skill_terms = ["react","javascript","html","css","shopify","liquid","api","bootstrap","tailwind","python","aws","docker"]
        return (',' in s and sum(1 for t in skill_terms if t in s.lower()) >= 4)
    
    def _lemmatize_light(self, s: str) -> str:
        """Light lemmatization for better matching"""
        return re.sub(r'(ing|ed|s)\b', '', s)
    
    def _role_blocks(self, text: str):
        """Extract role blocks with date ranges"""
        blocks, cur = [], {"lines": []}
        for line in text.splitlines():
            if re.search(DATE_RE, line.lower()):
                if cur["lines"]:
                    blocks.append(cur)
                    cur = {"lines": []}
                cur["header"] = line
                cur["start"], cur["end"], cur["current"] = self._parse_dates(line)
            else:
                cur["lines"].append(line)
        if cur["lines"]: 
            blocks.append(cur)
        return blocks
    
    def _evidence_score(self, sent: str, alias: str, sec_w: float) -> float:
        """Score evidence quality with multiple factors"""
        score = 0
        ns = self.normalize_text(sent)
        
        # String similarity
        score += max(fuzz.partial_ratio(ns, alias), fuzz.token_set_ratio(ns, alias)) / 100.0  # 0..1
        
        # Quality indicators
        if self._has_tools_and_actions(sent): 
            score += 0.4
        if self._has_metrics(sent): 
            score += 0.6
            
        # Recent year bonus
        y = datetime.now().year
        if str(y) in ns or str(y-1) in ns or "present" in ns or "current" in ns: 
            score += 0.25
            
        # Section weight favor Experience/Projects
        score *= (0.5 + sec_w)
        
        return score
        
    def expand_skill_to_subskills(self, skill_name: str) -> List[str]:
        """
        Break down a long skill definition like:
        'React.js Development (components, hooks, state management)'
        into ['react.js development', 'components', 'hooks', 'state management']
        """
        base = re.sub(r'\(.*?\)', '', skill_name).strip()
        inside = re.findall(r'\((.*?)\)', skill_name)
        subs = [base]
        
        if inside:
            for part in inside[0].split(','):
                cleaned = part.strip()
                if cleaned:
                    subs.append(cleaned)
        
        return subs
    
    def get_aliases_for_skill(self, skill_name: str) -> List[str]:
        """Get aliases for a skill name, handling parentheses & synonyms"""
        s = self.normalize_text(skill_name)
        
        # Direct hit in SKILL_ALIAS_MAP
        for k in SKILL_ALIAS_MAP:
            if self.normalize_text(k) == s:
                return SKILL_ALIAS_MAP[k]
        
        # Check for specific sub-skill matches
        if s in ['components', 'component']:
            return ['component', 'components', 'jsx', 'react component', 'ui component']
        elif s in ['hooks', 'hook']:
            return ['hooks', 'hook', 'usestate', 'useeffect', 'react hooks', 'custom hook']
        elif s in ['state management', 'state']:
            return ['state management', 'state', 'redux', 'context api', 'zustand', 'recoil']
        elif 'react' in s:
            return ['react', 'reactjs', 'react.js', 'jsx', 'react native']
        elif 'javascript' in s or 'js' in s:
            return ['javascript', 'js', 'es6', 'typescript', 'node.js']
        elif 'html' in s or 'css' in s:
            return ['html', 'html5', 'css', 'css3', 'responsive', 'mobile-first']
        elif 'api' in s:
            return ['api', 'rest api', 'graphql', 'webhook', 'integration']
        elif 'performance' in s:
            return ['performance', 'optimization', 'lighthouse', 'core web vitals', 'speed']
        
        # For sub-skills, check if any part matches main skills
        for k, aliases in SKILL_ALIAS_MAP.items():
            if s in self.normalize_text(k):
                return aliases
        
        # Fallback: derive from parentheses/tokens
        base = re.sub(r'[\(\)]', ' ', skill_name)
        tokens = [t.strip().lower() for t in re.split(r'[,/]|and|&', base) if t.strip()]
        # Add individual tokens as aliases
        derived = tokens + [skill_name.lower()]
        return list(dict.fromkeys(derived))
    
    def _sentences(self, text: str) -> List[str]:
        """Simple sentence splitter that keeps bullets/lines useful for CVs"""
        parts = re.split(r'[\n•\-–;.!?]', text)
        return [p.strip() for p in parts if len(p.strip()) > 6]
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for matching - lowercase and strip diacritics"""
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text
    
    def extract_experience_entries(self, cv_text: str) -> List[Dict]:
        """Extract work experience entries with dates"""
        entries = []
        
        # Look for experience sections
        lines = cv_text.split('\n')
        
        in_experience_section = False
        current_entry = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering experience section
            if re.search(r'(?:experience|employment|work history|professional experience)', line.lower()):
                in_experience_section = True
                continue
            
            # Check if we're leaving experience section
            if in_experience_section and re.search(r'(?:education|skills|projects|certifications)', line.lower()):
                in_experience_section = False
                continue
            
            if in_experience_section:
                # Look for job title patterns
                if '|' in line:  # Title | Company | Dates format
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:
                        title = parts[0]
                        company = parts[1]
                        dates = parts[2] if len(parts) > 2 else ""
                        
                        start_date, end_date, is_current = self._parse_dates(dates)
                        
                        entries.append({
                            'title': title,
                            'company': company,
                            'start': start_date,
                            'end': end_date,
                            'current': is_current,
                            'raw_text': line
                        })
        
        return entries
    
    def _parse_dates(self, date_str: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Parse date ranges from text"""
        date_str = date_str.lower()
        is_current = 'present' in date_str or 'current' in date_str
        
        # Extract years
        years = re.findall(r'20\d{2}', date_str)
        
        if not years:
            return None, None, is_current
            
        start_year = years[0] if years else None
        end_year = years[-1] if len(years) > 1 and not is_current else None
        
        return start_year, end_year, is_current
    
    def calculate_years_experience(self, cv_text: str) -> float:
        """Calculate total years of experience with overlaps handling"""
        entries = self.extract_experience_entries(cv_text)
        
        if not entries:
            # Fallback: look for experience mentions
            exp_matches = re.findall(r'(\d+)[\+\s]*years?\s+(?:of\s+)?experience', cv_text.lower())
            if exp_matches:
                return float(max(exp_matches))
            
            # Fallback: estimate from year ranges mentioned
            years = re.findall(r'20\d{2}', cv_text)
            if len(years) >= 2:
                start_year = min(int(y) for y in years)
                end_year = max(int(y) for y in years)
                return min(datetime.now().year - start_year, 20.0)
            
            return 2.0  # Default assumption
        
        total_months = 0
        current_year = datetime.now().year
        
        for entry in entries:
            if entry.get('start'):
                start_year = int(entry['start'])
            else:
                start_year = current_year - 2  # Default assumption
            
            if entry.get('current'):
                end_year = current_year
            elif entry.get('end'):
                end_year = int(entry['end'])
            else:
                end_year = start_year + 2  # Assume 2 years if no end date
            
            months = max(0, (end_year - start_year) * 12)
            total_months += months
        
        return min(total_months / 12.0, 20.0)  # Cap at 20 years
    
    def extract_evidence_with_confidence(self, skill: str, cv_text: str) -> Tuple[List[str], str]:
        """Extract evidence with improved ranking and section awareness"""
        # Get all sub-skills and their aliases
        subskills = self.expand_skill_to_subskills(skill)
        all_aliases = []
        for subskill in subskills:
            all_aliases.extend(self.get_aliases_for_skill(subskill))
        
        # Remove duplicates and normalize
        aliases = [self.normalize_text(a) for a in all_aliases]
        candidates = []

        for sent, sec_w in self._sentences_with_section(cv_text):
            # Skip skill dumps and already used evidence
            if self._is_skill_dump(sent) or hash(sent) in self.evidence_used:
                continue
                
            ns = self.normalize_text(sent)
            
            # Check for alias matches
            for alias in aliases:
                if (alias in ns) or (fuzz.partial_ratio(ns, alias) >= 86):
                    score = self._evidence_score(sent, alias, sec_w)
                    candidates.append((score, sent))
                    break
        
        # Sort by quality and take top 3
        candidates.sort(reverse=True)
        evidence = [s for _, s in candidates[:3]]
        
        # Mark evidence as used to prevent cross-skill leakage
        for ev in evidence:
            self.evidence_used.add(hash(ev))
        
        # Determine confidence level
        if any(self._has_metrics(e) for e in evidence): 
            conf = "E3"
        elif any(self._has_tools_and_actions(e) for e in evidence): 
            conf = "E2"
        else: 
            conf = "E1"
            
        return evidence, conf
    
    def _has_metrics(self, text: str) -> bool:
        """Check if text contains quantifiable metrics"""
        metric_patterns = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Money amounts
            r'\d+[kK][\+]?',  # Thousands (10k, 5K+)
            r'\d+[mM][\+]?',  # Millions
            r'\d+x',  # Multipliers (3x, 10x)
            r'increased.*\d+',  # Increased by number
            r'reduced.*\d+',  # Reduced by number
            r'improved.*\d+',  # Improved by number
            r'\d+.*(?:users|customers|leads|sales|revenue|traffic|conversion)',
            r'roas.*\d+',
            r'ctr.*\d+',
            r'cpa.*\d+'
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in metric_patterns)
    
    def _has_tools_and_actions(self, text: str) -> bool:
        """Check if text contains specific tools and actions"""
        tool_patterns = [
            r'(?:using|with|via|through|in)\s+\w+',
            r'\w+(?:\.js|\.py|\.css)',  # File extensions
            r'(?:google ads|facebook ads|klaviyo|mailchimp|hubspot|salesforce)',
            r'(?:react|reactjs|vue|angular|python|javascript|sql|redux|hooks)',
            r'(?:aws|azure|gcp|docker|kubernetes)',
            r'(?:shopify|wordpress|magento|woocommerce|liquid)',
            r'(?:built|created|developed|implemented|managed|optimized|increased|improved)',
            r'(?:ga4|google analytics|seo|ppc|automation)',
            r'(?:landing pages|campaigns|content calendar|email)',
            r'(?:components|jsx|typescript|api|rest|graphql)',
            r'(?:tailwind|bootstrap|css|html|responsive)',
            r'(?:stripe|razorpay|zapier|integration|performance)'
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in tool_patterns)
    
    def rate_skill_base(self, skill: str, evidence: List[str], confidence: str) -> float:
        """Rate skill using 0-10 rubric based on evidence with evidence floor"""
        if not evidence:
            return 0.0
        
        base = min(len(evidence) * 2.0, 6.0)
        has_metrics = any(self._has_metrics(ev) for ev in evidence)
        has_tools = any(self._has_tools_and_actions(ev) for ev in evidence)

        if has_metrics and has_tools:
            base = max(base, 7.0)
        elif has_tools:
            base = max(base, 5.0)  # Floor for real evidence
        else:
            base = max(base, 3.5)  # Weak evidence floor

        # Floor ratings when clear evidence exists - prevent 0/10 with real evidence
        if evidence and base < 3.0:
            base = 3.0

        if confidence == "E1":
            base = min(base, 6.0)  # Don't over-cap too harshly
        elif confidence == "E2":
            base = min(base, 7.5)

        return round(base, 1)
    
    def calculate_recency_factor(self, cv_text: str, skill: str) -> float:
        """Calculate recency factor based on last usage year"""
        # Get all sub-skills and their aliases
        subskills = self.expand_skill_to_subskills(skill)
        all_aliases = []
        for subskill in subskills:
            all_aliases.extend(self.get_aliases_for_skill(subskill))
        
        aliases = [self.normalize_text(a) for a in all_aliases]
        last_year = None
        
        # Find last usage year by checking lines with skill mentions
        for line in cv_text.splitlines():
            nl = self.normalize_text(line)
            if any(a in nl for a in aliases):
                years = re.findall(r'20\d{2}', nl)
                if years:
                    last_year = max(last_year or 0, int(max(years)))
        
        # Fallback if no year found
        if last_year is None:
            last_year = datetime.now().year - 2
            
        delta = max(0, datetime.now().year - last_year)
        return math.exp(-self.lambda_recency * min(delta, 6))
    
    def _get_skill_synonyms(self, skill: str) -> List[str]:
        """Get synonyms for a skill for context matching"""
        skill_lower = skill.lower()
        
        if 'seo' in skill_lower or 'content' in skill_lower:
            return ['seo', 'organic', 'search', 'content marketing']
        elif 'paid' in skill_lower or 'ads' in skill_lower:
            return ['google ads', 'facebook ads', 'ppc', 'paid', 'advertising']
        elif 'social' in skill_lower:
            return ['social media', 'instagram', 'facebook', 'linkedin', 'twitter']
        elif 'email' in skill_lower:
            return ['email', 'mailchimp', 'klaviyo', 'automation']
        elif 'react' in skill_lower:
            return ['react', 'jsx', 'frontend']
        elif 'javascript' in skill_lower:
            return ['javascript', 'js', 'frontend']
        
        return [skill_lower]
    
    def calculate_tenure_factor(self, skill: str, cv_text: str) -> float:
        """Calculate tenure factor by mapping skills to role blocks with real dates"""
        # Get all sub-skills and their aliases
        subskills = self.expand_skill_to_subskills(skill)
        all_aliases = []
        for subskill in subskills:
            all_aliases.extend(self.get_aliases_for_skill(subskill))
        
        aliases = [self.normalize_text(a) for a in all_aliases if len(a) > 2]
        months = 0
        
        for block in self._role_blocks(cv_text):
            body = ' '.join(block.get("lines", []))
            nb = self.normalize_text(body)
            
            # Check if this role block mentions the skill
            if any(a in nb for a in aliases):
                start_year = int(block["start"]) if block.get("start") else datetime.now().year - 2
                if block.get("current") or not block.get("end"):
                    end_year = datetime.now().year
                else:
                    end_year = int(block["end"])
                    
                months += max(0, (end_year - start_year) * 12)
        
        months = min(months, 60)  # Cap at 5 years
        return min(1.2, 0.8 + months / 36.0)
    
    def calculate_scope_bonus(self, evidence: List[str]) -> float:
        """Calculate scope/impact bonus based on evidence"""
        if not evidence:
            return 0.0
        
        bonus = 0.0
        
        for ev in evidence:
            ev_lower = ev.lower()
            
            # Check for material impact indicators
            if any(term in ev_lower for term in ['increased', 'improved', 'reduced', 'optimized']):
                if self._has_metrics(ev):
                    bonus += 0.3
            
            # Check for scale indicators
            if any(term in ev_lower for term in ['enterprise', 'million', 'scale', 'production']):
                bonus += 0.2
        
        return min(bonus, 0.5)  # Cap at +0.5
    
    def apply_seniority_penalty(self, job_profile: JobProfile, cv_text: str) -> float:
        """Apply seniority alignment penalty"""
        if job_profile.seniority != "senior":
            return 0.0
        
        # Check for leadership indicators
        leadership_indicators = [
            'led team', 'managed team', 'supervised', 'mentored',
            'strategic', 'strategy', 'architecture', 'design decisions'
        ]
        
        cv_lower = cv_text.lower()
        has_leadership = any(indicator in cv_lower for indicator in leadership_indicators)
        
        return 0.0 if has_leadership else -1.0
    
    def normalize_weights(self, job_profile: JobProfile) -> List[float]:
        """Normalize weights to sum to 1.0"""
        weights = [skill.weight for skill in job_profile.required_skills]
        total_weight = sum(weights)
        
        if total_weight == 0:
            # Equal weights if all zero
            return [1.0 / len(weights) for _ in weights]
        
        return [w / total_weight for w in weights]
    
    def analyze_skill(self, skill_name: str, weight: float, critical: bool, 
                     cv_text: str, job_profile: JobProfile) -> SkillRating:
        """Analyze a single skill and return rating with adjustments"""
        
        # Extract evidence and confidence
        evidence, confidence = self.extract_evidence_with_confidence(skill_name, cv_text)
        
        # Calculate base rating
        base_rating = self.rate_skill_base(skill_name, evidence, confidence)
        
        # Coverage bonus for multiple distinct alias hits
        subskills = self.expand_skill_to_subskills(skill_name)
        all_aliases = []
        for subskill in subskills:
            all_aliases.extend(self.get_aliases_for_skill(subskill))
        
        aliases = [self.normalize_text(a) for a in all_aliases]
        nc = self.normalize_text(cv_text)
        distinct_hits = len({a for a in aliases if a in nc})
        coverage_bonus = min(1.0, 0.3 * max(0, distinct_hits - 2))  # +0..1
        base_rating += coverage_bonus
        
        # Calculate adjustment factors
        recency_factor = self.calculate_recency_factor(cv_text, skill_name)
        tenure_factor = self.calculate_tenure_factor(skill_name, cv_text)
        scope_bonus = self.calculate_scope_bonus(evidence)
        seniority_penalty = self.apply_seniority_penalty(job_profile, cv_text)
        
        # Apply adjustments
        adjusted_rating = base_rating * recency_factor * tenure_factor
        adjusted_rating += scope_bonus + seniority_penalty
        
        # Evidence floor - don't punish real evidence
        if evidence and adjusted_rating < 4.5:
            adjusted_rating = 4.5
        
        # Cap at 10.0 and floor at 0.0
        pre_calibration = max(0.0, min(10.0, adjusted_rating))
        final_rating = calibrate_score(pre_calibration)
        
        # Generate reason for score
        reason = []
        if confidence == "E1": 
            reason.append("weak evidence")
        if recency_factor < 0.8: 
            reason.append("stale usage")
        if tenure_factor < 0.95: 
            reason.append("limited tenure")
        reason_str = ", ".join(reason) or "strong evidence"
        
        return SkillRating(
            skill=skill_name,
            weight=weight,
            critical=critical,
            rating=round(final_rating, 1),
            evidence_confidence=confidence,
            evidence=evidence,
            adjustments=SkillAdjustments(
                recency_factor=round(recency_factor, 3),
                tenure_factor=round(tenure_factor, 3),
                scope_bonus=round(scope_bonus, 1),
                seniority_penalty=round(seniority_penalty, 1)
            ),
            reason=reason_str
        )
    
    def apply_critical_skill_gates(self, ratings: List[SkillRating], 
                                 weighted_score: float) -> Tuple[float, str]:
        """Apply critical skill gating penalties with fair treatment"""
        gating_penalty = 1.0
        gate_reason = ""
        
        for rating in ratings:
            if rating.critical:
                # Treat "some alias evidence but low rating" as soft gate, not hard
                if rating.rating == 0 and not rating.evidence:
                    # Hard gate only for zero evidence
                    return min(weighted_score, 4.0), "hard_gate"
                elif rating.rating < 2.0:
                    # Soft gate for low ratings with some evidence
                    gating_penalty *= 0.85
                    gate_reason = "soft_gate"
                elif rating.rating < 4.0:
                    # Lighter soft gate
                    gating_penalty *= 0.9
                    gate_reason = "soft_gate"
        
        return weighted_score * gating_penalty, gate_reason
    
    def calculate_weighted_score(self, ratings: List[SkillRating], 
                               normalized_weights: List[float]) -> WeightedScore:
        """Calculate final weighted score"""
        total_score = sum(rating.rating * weight 
                         for rating, weight in zip(ratings, normalized_weights))
        
        # Apply critical skill gates
        gated_score, gate_reason = self.apply_critical_skill_gates(ratings, total_score)
        
        final_score = round(gated_score, 1)
        match_pct = round((final_score / 10.0) * 100)
        
        return WeightedScore(score_10=final_score, match_pct=match_pct)
    
    def analyze_ats_keywords(self, job_profile: JobProfile, cv_text: str) -> ATSKeywords:
        """Analyze ATS keyword coverage using aliases, fuzzy matching and lemmatization"""
        nc = self.normalize_text(cv_text)
        found, missing = [], []

        # Include required skills + must-have + nice-to-have
        all_keywords = [s.name for s in job_profile.required_skills]
        all_keywords += job_profile.must_have_keywords + job_profile.nice_to_have

        for kw in all_keywords:
            if kw in [s.name for s in job_profile.required_skills]:
                # For job skills, use sub-skill expansion
                subskills = self.expand_skill_to_subskills(kw)
                all_aliases = []
                for subskill in subskills:
                    all_aliases.extend(self.get_aliases_for_skill(subskill))
                aliases = [self.normalize_text(a) for a in all_aliases]
            else:
                # For other keywords, use direct normalization
                aliases = [self.normalize_text(kw)]
            
            # Check with exact, fuzzy, and lemmatized matching
            hit = False
            for alias in aliases:
                lhs = self._lemmatize_light(alias)
                rhs = self._lemmatize_light(nc)
                
                if (lhs in rhs) or (fuzz.token_set_ratio(lhs, rhs) >= 86):
                    hit = True
                    break
            
            (found if hit else missing).append(kw)

        return ATSKeywords(found=found, missing=missing)
    
    def detect_red_flags(self, cv_text: str, job_profile: JobProfile, 
                        ratings: List[SkillRating]) -> List[str]:
        """Detect red flags in CV"""
        red_flags = []
        
        # No evidence for high-weight skills
        high_weight_skills_no_evidence = [
            r.skill for r in ratings 
            if r.weight >= 0.25 and r.rating <= 2.0
        ]
        if len(high_weight_skills_no_evidence) >= 2:
            red_flags.append(f"No evidence for high-weight skills: {', '.join(high_weight_skills_no_evidence[:2])}")
        
        # Grandiose claims without metrics
        grandiose_patterns = [
            r'10x revenue', r'doubled sales', r'transformed', r'revolutionized'
        ]
        cv_lower = cv_text.lower()
        for pattern in grandiose_patterns:
            if re.search(pattern, cv_lower) and not self._has_metrics(cv_text):
                red_flags.append("Grandiose claims without supporting metrics")
                break
        
        # Job hopping detection
        experience_entries = self.extract_experience_entries(cv_text)
        short_tenures = [e for e in experience_entries 
                        if e.get('start') and e.get('end') and 
                        int(e['end']) - int(e['start']) < 1]
        
        if len(short_tenures) >= 4:
            red_flags.append(f"Job hopping pattern: {len(short_tenures)} roles under 1 year")
        
        # Missing portfolio/links for technical roles
        if any(term in job_profile.title.lower() for term in ['developer', 'designer', 'engineer']):
            if not re.search(r'https?://|github|portfolio|linkedin', cv_text.lower()):
                red_flags.append("No portfolio or professional links found")
        
        return red_flags[:5]  # Limit to top 5
    
    def generate_narrative_output(self, analysis: AnalysisResult, 
                                cv_text: str) -> str:
        """Generate markdown narrative output"""
        
        candidate_name = analysis.candidate.name or "Candidate"
        job_title = analysis.job_profile['title']
        
        markdown = f"""# Candidate Analysis: {candidate_name} — {job_title}

## Summary
Professional candidate with {analysis.candidate.years_experience:.1f} years of experience. Analysis shows {analysis.weighted_score.match_pct}% alignment with role requirements based on evidence-driven skill assessment.

## Skills & Evidence
"""
        
        for rating in analysis.ratings:
            critical_badge = " (Critical)" if rating.critical else ""
            markdown += f"- **{rating.skill}** (Weight: {rating.weight:.1f}){critical_badge} — Rating: {rating.rating}/10 — {rating.evidence_confidence} evidence\n"
            for evidence in rating.evidence[:2]:
                markdown += f"  - {evidence[:80]}...\n" if len(evidence) > 80 else f"  - {evidence}\n"
        
        markdown += f"""
## Weighted Score
**{analysis.weighted_score.score_10}/10** (~{analysis.weighted_score.match_pct}% match)

## Career Highlights
"""
        for highlight in analysis.highlights:
            markdown += f"- {highlight}\n"
        
        markdown += "\n## Pros\n"
        for pro in analysis.pros:
            markdown += f"- {pro}\n"
        
        markdown += "\n## Cons\n"
        for con in analysis.cons:
            markdown += f"- {con}\n"
        
        markdown += f"""
## ATS Keyword Coverage
- **Found ({len(analysis.ats_keywords.found)}):** {', '.join(analysis.ats_keywords.found[:5])}{'...' if len(analysis.ats_keywords.found) > 5 else ''}
- **Missing ({len(analysis.ats_keywords.missing)}):** {', '.join(analysis.ats_keywords.missing[:5])}{'...' if len(analysis.ats_keywords.missing) > 5 else ''}

## Growth Plan
"""
        for step in analysis.growth_plan:
            markdown += f"- {step}\n"
        
        markdown += f"""
## Fit Assessment
**{analysis.fit_assessment.label.title()}** — {analysis.fit_assessment.reason}

## Best Role Fit
"""
        for role in analysis.best_role_fit:
            markdown += f"- {role}\n"
        
        if analysis.red_flags:
            markdown += "\n## Red Flags\n"
            for flag in analysis.red_flags:
                markdown += f"- {flag}\n"
        
        return markdown
    
    def generate_highlights_pros_cons(self, cv_text: str, ratings: List[SkillRating],
                                    job_profile: JobProfile) -> Tuple[List[str], List[str], List[str]]:
        """Generate highlights, pros, and cons"""
        
        # Highlights - extract concrete achievements
        highlights = []
        sentences = re.split(r'[.!?;]', cv_text)
        for sentence in sentences:
            if self._has_metrics(sentence) and len(sentence.strip()) > 20:
                highlights.append(sentence.strip())
            if len(highlights) >= 3:
                break
        
        if not highlights:
            highlights = ["Professional experience in target domain"]
        
        # Pros - based on strong skills
        pros = []
        strong_skills = [r for r in ratings if r.rating >= 7.0]
        if strong_skills:
            pros.append(f"Strong expertise in {strong_skills[0].skill}")
        
        if any(r.evidence_confidence == "E3" for r in ratings):
            pros.append("Quantifiable achievements with measurable impact")
        
        experience_years = self.calculate_years_experience(cv_text)
        if experience_years >= 3:
            pros.append(f"Solid professional experience ({experience_years:.1f} years)")
        
        if re.search(r'https?://|github|portfolio', cv_text.lower()):
            pros.append("Professional online presence with portfolio/links")
        
        pros.extend(["Relevant domain experience", "Technical competency demonstrated"])
        
        # Cons - based on weak skills and gaps
        cons = []
        weak_skills = [r for r in ratings if r.rating < 4.0]
        if weak_skills:
            cons.append(f"Limited evidence for {weak_skills[0].skill}")
        
        missing_critical = [r for r in ratings if r.critical and r.rating < 4.0]
        if missing_critical:
            cons.append(f"Below threshold in critical skill: {missing_critical[0].skill}")
        
        if experience_years < 2:
            cons.append("Limited professional experience")
        
        if not re.search(r'portfolio|github', cv_text.lower()):
            cons.append("No technical portfolio or code samples provided")
        
        cons.extend(["May require skill development in weaker areas", "Experience depth varies by skill area"])
        
        return highlights[:3], pros[:6], cons[:6]
    
    def generate_growth_plan(self, ratings: List[SkillRating], 
                           job_profile: JobProfile) -> List[str]:
        """Generate growth plan recommendations"""
        plan = []
        
        # Focus on weakest high-weight skills
        weak_important_skills = [
            r for r in ratings 
            if r.weight >= 0.2 and r.rating < 6.0
        ]
        
        weak_important_skills.sort(key=lambda x: (x.weight, -x.rating), reverse=True)
        
        for skill in weak_important_skills[:2]:
            plan.append(f"Develop {skill.skill} through hands-on projects with measurable outcomes")
        
        # Add general recommendations
        plan.append("Build portfolio showcasing relevant work with metrics and impact")
        plan.append("Pursue certifications or training in identified skill gaps")
        
        return plan[:4]
    
    def determine_fit_assessment(self, weighted_score: WeightedScore, 
                               ratings: List[SkillRating]) -> FitAssessment:
        """Determine overall fit assessment"""
        score = weighted_score.score_10
        
        # Check critical skill failures
        critical_failures = [r for r in ratings if r.critical and r.rating < 4.0]
        
        if critical_failures or score < 4.0:
            return FitAssessment(
                label="poor",
                reason="Below threshold in critical skills or overall low match"
            )
        elif score >= 7.0:
            return FitAssessment(
                label="good", 
                reason="Strong alignment with role requirements and evidence"
            )
        else:
            return FitAssessment(
                label="partial",
                reason="Moderate alignment with some skill gaps to address"
            )
    
    def suggest_best_roles(self, ratings: List[SkillRating], 
                          experience_years: float) -> List[str]:
        """Suggest best fitting roles based on skill strengths"""
        roles = []
        
        # Analyze skill strengths
        strong_skills = [r.skill for r in ratings if r.rating >= 7.0]
        
        if not strong_skills:
            strong_skills = [r.skill for r in ratings if r.rating >= 5.0]
        
        # Role mapping based on skills
        role_mappings = {
            'seo': ['SEO Specialist', 'Content Marketing Manager', 'Digital Marketing Specialist'],
            'paid_ads': ['PPC Specialist', 'Digital Advertising Manager', 'Performance Marketing Manager'],
            'social_media': ['Social Media Manager', 'Community Manager', 'Content Creator'],
            'email_marketing': ['Email Marketing Specialist', 'Marketing Automation Manager'],
            'python': ['Python Developer', 'Data Analyst', 'Backend Developer'],
            'react': ['Frontend Developer', 'React Developer', 'UI Developer'],
            'machine_learning': ['Data Scientist', 'ML Engineer', 'AI Researcher'],
            'leadership': ['Team Lead', 'Technical Manager', 'Project Manager']
        }
        
        # Match skills to roles
        for skill in strong_skills[:2]:
            skill_lower = skill.lower()
            for key, role_list in role_mappings.items():
                if key in skill_lower:
                    roles.extend(role_list)
        
        # Add seniority prefix
        seniority_prefix = ""
        if experience_years >= 7:
            seniority_prefix = "Senior "
        elif experience_years >= 3:
            seniority_prefix = "Mid-Level "
        elif experience_years < 2:
            seniority_prefix = "Junior "
        
        roles = [seniority_prefix + role for role in roles]
        
        # Remove duplicates and limit
        roles = list(dict.fromkeys(roles))[:4]
        
        if not roles:
            roles = ["General Specialist", "Professional Role"]
        
        return roles
    
    def analyze_candidate(self, cv_content: str, job_profile: JobProfile,
                         candidate_id: str = "unknown") -> AnalysisResult:
        """
        Main analysis method - analyzes CV against job profile
        Returns complete AnalysisResult following specification
        """
        
        # Reset evidence tracking for each analysis
        self.evidence_used.clear()
        
        # Extract candidate info
        experience_years = self.calculate_years_experience(cv_content)
        candidate_name = self._extract_candidate_name(cv_content)
        
        candidate = CandidateAnalysis(
            name=candidate_name,
            years_experience=experience_years,
            locale=job_profile.locale
        )
        
        # Normalize weights
        normalized_weights = self.normalize_weights(job_profile)
        
        # Analyze each skill
        ratings = []
        for i, skill_def in enumerate(job_profile.required_skills):
            rating = self.analyze_skill(
                skill_def.name, 
                normalized_weights[i],
                skill_def.critical,
                cv_content,
                job_profile
            )
            ratings.append(rating)
        
        # Calculate weighted score
        weighted_score = self.calculate_weighted_score(ratings, normalized_weights)
        
        # Generate narrative components
        highlights, pros, cons = self.generate_highlights_pros_cons(cv_content, ratings, job_profile)
        growth_plan = self.generate_growth_plan(ratings, job_profile)
        fit_assessment = self.determine_fit_assessment(weighted_score, ratings)
        best_roles = self.suggest_best_roles(ratings, experience_years)
        
        # Analyze ATS keywords
        ats_keywords = self.analyze_ats_keywords(job_profile, cv_content)
        
        # Detect red flags
        red_flags = self.detect_red_flags(cv_content, job_profile, ratings)
        
        return AnalysisResult(
            candidate=candidate,
            job_profile={
                "title": job_profile.title,
                "seniority": job_profile.seniority,
                "skills": [{"name": s.name, "weight": w, "critical": s.critical} 
                          for s, w in zip(job_profile.required_skills, normalized_weights)]
            },
            ratings=ratings,
            weighted_score=weighted_score,
            highlights=highlights,
            pros=pros,
            cons=cons,
            ats_keywords=ats_keywords,
            growth_plan=growth_plan,
            fit_assessment=fit_assessment,
            best_role_fit=best_roles,
            red_flags=red_flags
        )
    
    def _extract_candidate_name(self, cv_text: str) -> Optional[str]:
        """Extract candidate name from CV"""
        lines = cv_text.split('\n')[:5]  # Check first 5 lines
        
        for line in lines:
            line = line.strip()
            # Simple heuristic: first line that looks like a name
            if (len(line.split()) == 2 and 
                not any(char in line for char in '@(){}[]') and
                not re.search(r'\d', line) and
                len(line) < 50):
                return line
        
        return None

# Global instance
cv_analyzer = CVAnalyzerAgent()
