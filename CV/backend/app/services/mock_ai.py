"""
Mock AI service for testing when OpenAI quota is exceeded
"""

from app.schemas import JobProfile, CandidateResult
import json
import re
from typing import List, Dict, Tuple

def analyze_skill_match(skill_name: str, cv_content: str) -> Tuple[float, List[str]]:
    """
    Enhanced skill analysis with precise pattern matching and achievement extraction
    Returns (match_score, evidence_list)
    """
    skill_lower = skill_name.lower()
    cv_lower = cv_content.lower()
    
    # Enhanced skill pattern generation
    patterns = generate_enhanced_skill_patterns(skill_name)
    
    # Find high-quality evidence with context scoring
    evidence = []
    match_count = 0
    context_matches = []
    
    for pattern in patterns:
        # Find technical achievements and specific implementations
        achievement_contexts = find_achievement_contexts(pattern, cv_content)
        quantified_experiences = find_quantified_experiences(pattern, cv_content)
        project_implementations = find_project_implementations(pattern, cv_content)
        
        # Combine all evidence types
        all_contexts = achievement_contexts + quantified_experiences + project_implementations
        
        for context in all_contexts:
            match_count += 1
            if context not in context_matches and len(context.strip()) > 20:
                context_matches.append(context)
    
    # Score evidence quality and relevance
    scored_evidence = []
    for context in context_matches:
        quality_score = calculate_evidence_quality(context, skill_name)
        scored_evidence.append((context, quality_score))
    
    # Sort by quality and take best evidence
    scored_evidence.sort(key=lambda x: x[1], reverse=True)
    evidence = [ctx for ctx, score in scored_evidence[:4] if score > 0.3]
    
    # Enhanced scoring with quality weighting
    if match_count == 0:
        score = 0.0
    elif not evidence:  # Matches found but low quality
        score = 0.1
    else:
        # Weight by evidence quality and quantity
        avg_quality = sum(score for _, score in scored_evidence[:4]) / min(4, len(scored_evidence))
        quantity_factor = min(match_count / 3, 1.0)  # Normalize to max 1.0
        score = min(avg_quality * quantity_factor * 0.9, 0.9)  # Cap at 0.9
    
    return score, evidence


def generate_enhanced_skill_patterns(skill_name: str) -> List[str]:
    """Generate comprehensive skill patterns including modern technologies"""
    skill_lower = skill_name.lower().strip()
    patterns = [skill_lower]
    
    # Enhanced technology variations with 2024-2025 updates
    tech_variations = {
        'javascript': ['js', 'es6', 'es2015', 'es2020', 'es2023', 'node.js', 'nodejs', 'typescript integration'],
        'python': ['py', 'python3', 'python3.11', 'python3.12', 'django', 'flask', 'fastapi', 'pydantic'],
        'react': ['reactjs', 'react.js', 'jsx', 'react hooks', 'react 18', 'next.js', 'remix'],
        'angular': ['angular 15', 'angular 16', 'angular 17', 'angularjs', 'standalone components'],
        'vue': ['vue 3', 'composition api', 'nuxt 3', 'pinia'],
        'machine learning': ['ml', 'llm', 'large language models', 'chatgpt', 'gpt', 'transformers', 'langchain'],
        'ai': ['artificial intelligence', 'generative ai', 'prompt engineering', 'rag', 'vector databases'],
        'cloud platforms': ['aws', 'azure', 'gcp', 'google cloud', 'serverless', 'edge computing'],
        'docker & kubernetes': ['containers', 'k8s', 'helm', 'docker compose', 'microservices'],
        'devops': ['ci/cd', 'github actions', 'gitlab ci', 'terraform', 'ansible', 'infrastructure as code'],
        'data science': ['pandas', 'numpy', 'scikit-learn', 'pytorch', 'tensorflow', 'jupyter'],
        'mobile development': ['react native', 'flutter', 'swift', 'kotlin', 'expo'],
        'web3': ['blockchain', 'smart contracts', 'solidity', 'web3.js', 'ethereum'],
        'ui/ux design': ['figma', 'sketch', 'adobe xd', 'prototyping', 'user research', 'design systems'],
        'salesforce': ['apex', 'lightning', 'salesforce dx', 'lwc', 'flow builder'],
        'product management': ['roadmap', 'agile', 'scrum', 'user stories', 'a/b testing', 'analytics'],
        'digital marketing': ['seo', 'sem', 'google ads', 'facebook ads', 'content marketing', 'email marketing'],
    }
    
    # Add variations for the skill
    for main_skill, variations in tech_variations.items():
        if main_skill in skill_lower or any(var in skill_lower for var in variations):
            patterns.extend(variations)
    
    # Add compound patterns
    if 'frontend' in skill_lower or 'front-end' in skill_lower:
        patterns.extend(['react', 'vue', 'angular', 'javascript', 'typescript', 'css', 'html'])
    
    if 'backend' in skill_lower or 'back-end' in skill_lower:
        patterns.extend(['node.js', 'python', 'java', 'api', 'database', 'server'])
    
    if 'full stack' in skill_lower or 'fullstack' in skill_lower:
        patterns.extend(['frontend', 'backend', 'database', 'api', 'deployment'])
    
    return list(set(patterns))  # Remove duplicates


def find_achievement_contexts(pattern: str, cv_content: str) -> List[str]:
    """Find contexts that show specific achievements or implementations"""
    achievement_indicators = [
        r'(built|developed|created|implemented|designed|architected|launched|deployed|optimized|improved|increased|reduced|achieved|delivered|led|managed)\s+[^.!?]*' + re.escape(pattern) + r'[^.!?]*[.!?]',
        r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*(resulting in|leading to|achieving|improving|increasing|reducing)[^.!?]*[.!?]',
        r'[^.!?]*\d+[\%\+\-\$][^.!?]*' + re.escape(pattern) + r'[^.!?]*[.!?]',  # Quantified results
        r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*\d+[\%\+\-\$][^.!?]*[.!?]'   # Pattern with numbers
    ]
    
    contexts = []
    for indicator in achievement_indicators:
        matches = re.finditer(indicator, cv_content, re.IGNORECASE)
        for match in matches:
            context = match.group(0).strip()
            if len(context) > 30 and len(context) < 200:  # Filter appropriate length
                contexts.append(context)
    
    return contexts


def find_quantified_experiences(pattern: str, cv_content: str) -> List[str]:
    """Find experiences with quantifiable metrics"""
    quantified_patterns = [
        r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*(\d+\%|\d+\+|\$\d+|x\d+|\d+x|\d+k|\d+m)[^.!?]*[.!?]',
        r'[^.!?]*(\d+\%|\d+\+|\$\d+|x\d+|\d+x|\d+k|\d+m)[^.!?]*' + re.escape(pattern) + r'[^.!?]*[.!?]',
        r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*(\d+\s+(years?|months?|weeks?|days?))[^.!?]*[.!?]'
    ]
    
    contexts = []
    for qpattern in quantified_patterns:
        matches = re.finditer(qpattern, cv_content, re.IGNORECASE)
        for match in matches:
            context = match.group(0).strip()
            if len(context) > 25 and len(context) < 180:
                contexts.append(context)
    
    return contexts


def find_project_implementations(pattern: str, cv_content: str) -> List[str]:
    """Find specific project implementations and technical details"""
    project_indicators = [
        r'(project|application|system|platform|tool|framework|library|module|component|feature)[^.!?]*' + re.escape(pattern) + r'[^.!?]*[.!?]',
        r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*(project|application|system|platform|tool|framework|library|module|component|feature)[^.!?]*[.!?]',
        r'(using|with|implementing|integrating|utilizing)[^.!?]*' + re.escape(pattern) + r'[^.!?]*[.!?]',
        r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*(integration|implementation|development|deployment)[^.!?]*[.!?]'
    ]
    
    contexts = []
    for indicator in project_indicators:
        matches = re.finditer(indicator, cv_content, re.IGNORECASE)
        for match in matches:
            context = match.group(0).strip()
            if len(context) > 20 and len(context) < 150:
                contexts.append(context)
    
    return contexts


def calculate_evidence_quality(evidence: str, skill_name: str) -> float:
    """Calculate quality score for evidence based on specificity and relevance"""
    score = 0.5  # Base score
    evidence_lower = evidence.lower()
    skill_lower = skill_name.lower()
    
    # Bonus for quantifiable achievements
    if re.search(r'\d+[\%\+\-\$]|\d+\s*(years?|months?|k|m|x)', evidence_lower):
        score += 0.3
    
    # Bonus for action verbs indicating hands-on experience
    action_verbs = ['built', 'developed', 'created', 'implemented', 'designed', 'architected', 'launched', 'deployed', 'optimized', 'led', 'managed']
    if any(verb in evidence_lower for verb in action_verbs):
        score += 0.2
    
    # Bonus for technical specificity
    technical_terms = ['api', 'database', 'framework', 'library', 'integration', 'deployment', 'optimization', 'architecture', 'system', 'platform']
    if any(term in evidence_lower for term in technical_terms):
        score += 0.15
    
    # Penalty for generic/vague statements
    generic_terms = ['familiar with', 'knowledge of', 'basic understanding', 'some experience', 'worked on']
    if any(term in evidence_lower for term in generic_terms):
        score -= 0.2
    
    # Penalty for very short or repetitive evidence
    if len(evidence) < 40:
        score -= 0.1
    
    # Bonus for direct skill mention
    if skill_lower in evidence_lower:
        score += 0.1
    
    return max(0.0, min(1.0, score))  # Clamp between 0 and 1


def generate_skill_patterns(skill_name: str) -> List[str]:
    """Generate skill patterns for matching - simplified version for compatibility"""
    skill_lower = skill_name.lower().strip()
    patterns = [skill_lower]
    
    # Basic variations
    if ' ' in skill_lower:
        patterns.append(skill_lower.replace(' ', ''))
        patterns.append(skill_lower.replace(' ', '-'))
    
    return patterns


def calculate_years_of_experience(cv_content: str) -> int:
    """
    Enhanced experience calculation with career progression analysis
    """
    cv_lower = cv_content.lower()
    
    # Look for explicit experience statements first
    explicit_patterns = [
        r'(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)',
        r'(\d+)\+?\s*years?\s*in\s+',
        r'over\s+(\d+)\s*years?',
        r'more than\s+(\d+)\s*years?',
        r'(\d+)\+\s*years?'
    ]
    
    max_explicit = 0
    for pattern in explicit_patterns:
        matches = re.findall(pattern, cv_lower)
        for match in matches:
            years = int(match[0] if isinstance(match, tuple) else match)
            max_explicit = max(max_explicit, years)
    
    if max_explicit > 0:
        return min(max_explicit, 20)  # Cap at 20 years
    
    # Analyze employment history with enhanced date recognition
    employment_years = analyze_employment_timeline(cv_content)
    if employment_years > 0:
        return employment_years
    
    # Fallback to skill-based estimation
    return estimate_experience_from_skills(cv_content)


def analyze_employment_timeline(cv_content: str) -> int:
    """Analyze employment dates to calculate experience"""
    import datetime
    
    # Enhanced date patterns
    date_patterns = [
        r'(\d{4})\s*[-–—]\s*(\d{4}|present|current)',
        r'(\w+)\s+(\d{4})\s*[-–—]\s*(\w+)?\s*(\d{4}|present|current)',
        r'(\d{1,2})/(\d{4})\s*[-–—]\s*(\d{1,2})/(\d{4}|present|current)',
        r'(\d{4})\s*to\s*(\d{4}|present|current)'
    ]
    
    positions = []
    current_year = datetime.datetime.now().year
    
    for pattern in date_patterns:
        matches = re.findall(pattern, cv_content, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 2:  # Simple year range
                    start_year = int(match[0])
                    end_year = current_year if match[1].lower() in ['present', 'current'] else int(match[1])
                elif len(match) == 4:  # Month year format
                    start_year = int(match[1])
                    end_year = current_year if match[3].lower() in ['present', 'current'] else int(match[3])
                else:
                    continue
                
                if 1990 <= start_year <= current_year and start_year <= end_year <= current_year + 1:
                    positions.append((start_year, end_year))
            except (ValueError, IndexError):
                continue
    
    if not positions:
        return 0
    
    # Calculate total experience considering overlaps
    positions.sort()
    merged_periods = []
    
    for start, end in positions:
        if not merged_periods or start > merged_periods[-1][1]:
            merged_periods.append((start, end))
        else:
            # Merge overlapping periods
            merged_periods[-1] = (merged_periods[-1][0], max(merged_periods[-1][1], end))
    
    total_years = sum(end - start for start, end in merged_periods)
    return min(total_years, 25)  # Cap at 25 years


def estimate_experience_from_skills(cv_content: str) -> int:
    """Estimate experience based on skill complexity and diversity"""
    cv_lower = cv_content.lower()
    
    # Advanced skills that typically indicate senior experience
    senior_skills = [
        'architecture', 'system design', 'team lead', 'technical lead', 'senior',
        'principal', 'staff', 'management', 'strategy', 'mentoring', 'scaling',
        'microservices', 'distributed systems', 'performance optimization'
    ]
    
    # Mid-level skills
    mid_skills = [
        'ci/cd', 'testing', 'deployment', 'database design', 'api design',
        'code review', 'agile', 'scrum', 'project management'
    ]
    
    # Technology diversity indicators
    tech_categories = {
        'languages': ['python', 'javascript', 'java', 'c#', 'php', 'ruby', 'go'],
        'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring'],
        'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
        'tools': ['git', 'jenkins', 'terraform', 'ansible']
    }
    
    senior_count = sum(1 for skill in senior_skills if skill in cv_lower)
    mid_count = sum(1 for skill in mid_skills if skill in cv_lower)
    
    # Count technology diversity
    diversity_score = 0
    for category, techs in tech_categories.items():
        category_count = sum(1 for tech in techs if tech in cv_lower)
        if category_count > 0:
            diversity_score += min(category_count, 3)  # Cap per category
    
    # Estimate based on skill complexity
    if senior_count >= 3 and diversity_score >= 8:
        return 8  # Senior level
    elif senior_count >= 1 and mid_count >= 2 and diversity_score >= 6:
        return 5  # Mid level
    elif mid_count >= 1 and diversity_score >= 3:
        return 3  # Junior-mid level
    elif diversity_score >= 1:
        return 1  # Entry level
    else:
        return 0  # Insufficient information


def detect_red_flags(cv_content: str, job_requirements: List[str]) -> List[str]:
    """
    Enhanced red flags detection with sophisticated analysis
    """
    red_flags = []
    cv_lower = cv_content.lower()
    
    # 1. Employment gaps detection
    gaps = detect_employment_gaps(cv_content)
    for gap in gaps:
        if gap['duration_months'] > 12:
            red_flags.append(f"Employment gap: {gap['duration_months']} months ({gap['period']})")
    
    # 2. Job hopping pattern
    job_tenure = analyze_job_tenure(cv_content)
    if job_tenure['avg_tenure'] < 1.5 and job_tenure['job_count'] >= 3:
        red_flags.append(f"Frequent job changes: {job_tenure['job_count']} jobs, avg {job_tenure['avg_tenure']:.1f} years each")
    
    # 3. Skill claims vs evidence inconsistencies
    inconsistencies = detect_skill_inconsistencies(cv_content, job_requirements)
    red_flags.extend(inconsistencies)
    
    # 4. Overqualification detection
    overqualification = detect_overqualification(cv_content, job_requirements)
    if overqualification:
        red_flags.append(overqualification)
    
    # 5. Missing critical information
    missing_info = detect_missing_information(cv_content)
    red_flags.extend(missing_info)
    
    # 6. Experience level mismatches
    experience_mismatches = detect_experience_mismatches(cv_content)
    red_flags.extend(experience_mismatches)
    
    return red_flags[:5]  # Return top 5 most critical


def detect_employment_gaps(cv_content: str) -> List[Dict]:
    """Detect gaps in employment history"""
    import datetime
    
    positions = []
    date_patterns = [
        r'(\d{4})\s*[-–—]\s*(\d{4}|present|current)',
        r'(\w+)\s+(\d{4})\s*[-–—]\s*(\w+)?\s*(\d{4}|present|current)'
    ]
    
    current_year = datetime.datetime.now().year
    
    for pattern in date_patterns:
        matches = re.findall(pattern, cv_content, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 2:
                    start_year = int(match[0])
                    end_year = current_year if match[1].lower() in ['present', 'current'] else int(match[1])
                else:
                    start_year = int(match[1])
                    end_year = current_year if match[3].lower() in ['present', 'current'] else int(match[3])
                
                if 1990 <= start_year <= current_year:
                    positions.append((start_year, end_year))
            except (ValueError, IndexError):
                continue
    
    if len(positions) < 2:
        return []
    
    positions.sort()
    gaps = []
    
    for i in range(len(positions) - 1):
        current_end = positions[i][1]
        next_start = positions[i + 1][0]
        
        if next_start > current_end:
            gap_months = (next_start - current_end) * 12
            if gap_months > 3:  # Only flag gaps > 3 months
                gaps.append({
                    'duration_months': gap_months,
                    'period': f"{current_end}-{next_start}"
                })
    
    return gaps


def analyze_job_tenure(cv_content: str) -> Dict:
    """Analyze job tenure patterns"""
    import datetime
    
    positions = []
    date_patterns = [
        r'(\d{4})\s*[-–—]\s*(\d{4}|present|current)',
        r'(\w+)\s+(\d{4})\s*[-–—]\s*(\w+)?\s*(\d{4}|present|current)'
    ]
    
    current_year = datetime.datetime.now().year
    
    for pattern in date_patterns:
        matches = re.findall(pattern, cv_content, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 2:
                    start_year = int(match[0])
                    end_year = current_year if match[1].lower() in ['present', 'current'] else int(match[1])
                else:
                    start_year = int(match[1])
                    end_year = current_year if match[3].lower() in ['present', 'current'] else int(match[3])
                
                if 1990 <= start_year <= current_year and start_year <= end_year:
                    duration = end_year - start_year
                    positions.append(duration)
            except (ValueError, IndexError):
                continue
    
    if not positions:
        return {'avg_tenure': 0, 'job_count': 0}
    
    avg_tenure = sum(positions) / len(positions)
    return {'avg_tenure': avg_tenure, 'job_count': len(positions)}


def detect_skill_inconsistencies(cv_content: str, job_requirements: List[str]) -> List[str]:
    """Detect inconsistencies between claimed skills and evidence"""
    inconsistencies = []
    cv_lower = cv_content.lower()
    
    # Check for unsupported senior claims
    senior_claims = ['expert', 'advanced', 'senior', 'lead', 'architect', 'specialist']
    experience_years = calculate_years_of_experience(cv_content)
    
    for claim in senior_claims:
        if claim in cv_lower and experience_years < 3:
            inconsistencies.append(f"Claims {claim} level with only {experience_years} years experience")
    
    # Check for technology mismatches
    conflicting_techs = {
        'angular': ['vue', 'react'],  # Usually specialize in one
        'ios': ['android'],  # Cross-platform is less common
        'mysql': ['mongodb']  # Different paradigms
    }
    
    for tech, conflicts in conflicting_techs.items():
        if tech in cv_lower:
            conflict_count = sum(1 for conflict in conflicts if conflict in cv_lower)
            if conflict_count >= 2:
                inconsistencies.append(f"Claims expertise in conflicting technologies: {tech} + {conflicts}")
    
    return inconsistencies


def detect_overqualification(cv_content: str, job_requirements: List[str]) -> str:
    """Detect if candidate might be overqualified"""
    cv_lower = cv_content.lower()
    experience_years = calculate_years_of_experience(cv_content)
    
    # Check for leadership roles in non-leadership positions
    leadership_indicators = ['ceo', 'cto', 'vp', 'director', 'head of', 'chief', 'founder']
    has_leadership = any(indicator in cv_lower for indicator in leadership_indicators)
    
    if has_leadership and experience_years > 10:
        return f"Senior leadership background ({experience_years} years) may be overqualified"
    
    # Check education level vs role requirements
    advanced_education = ['phd', 'ph.d', 'doctorate', 'mba']
    has_advanced_education = any(edu in cv_lower for edu in advanced_education)
    
    if has_advanced_education and 'senior' not in ' '.join(job_requirements).lower():
        return "Advanced degree holder for non-senior position"
    
    return ""


def detect_missing_information(cv_content: str) -> List[str]:
    """Detect missing critical information"""
    missing = []
    cv_lower = cv_content.lower()
    
    # Check for contact information
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
    
    if not re.search(email_pattern, cv_content):
        missing.append("No email address provided")
    
    if not re.search(phone_pattern, cv_content):
        missing.append("No phone number provided")
    
    # Check for employment dates
    date_pattern = r'\d{4}'
    if len(re.findall(date_pattern, cv_content)) < 2:
        missing.append("Limited or missing employment dates")
    
    # Check for education information
    education_keywords = ['university', 'college', 'degree', 'bachelor', 'master', 'education']
    if not any(keyword in cv_lower for keyword in education_keywords):
        missing.append("No education information provided")
    
    return missing


def detect_experience_mismatches(cv_content: str) -> List[str]:
    """Detect mismatches in claimed vs demonstrated experience"""
    mismatches = []
    cv_lower = cv_content.lower()
    experience_years = calculate_years_of_experience(cv_content)
    
    # Check for unrealistic skill claims vs experience
    complex_skills = ['system architecture', 'distributed systems', 'team leadership', 'technical strategy']
    complex_skill_count = sum(1 for skill in complex_skills if skill in cv_lower)
    
    if complex_skill_count >= 2 and experience_years < 5:
        mismatches.append(f"Claims complex skills ({complex_skill_count}) with limited experience ({experience_years} years)")
    
    # Check for technology breadth vs depth
    tech_count = len(re.findall(r'\b(python|java|javascript|react|angular|vue|aws|docker|kubernetes)\b', cv_lower))
    if tech_count > 15 and experience_years < 8:
        mismatches.append(f"Claims expertise in {tech_count} technologies with {experience_years} years experience")
    
    return mismatches


def extract_candidate_contact_info(cv_content: str) -> Dict[str, str]:
    """
    Extract candidate contact information from CV
    """
    contact_info = {
        'name': 'Unknown',
        'email': 'Not provided',
        'phone': 'Not provided',
        'location': 'Not provided'
    }
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, cv_content)
    if email_match:
        contact_info['email'] = email_match.group()
    
    # Extract phone number
    phone_patterns = [
        r'[\+]?[1-9]?[0-9]{7,15}',
        r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        r'\+[1-9]\d{1,14}'
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, cv_content)
        if phone_match:
            contact_info['phone'] = phone_match.group()
            break
    
    # Extract name (heuristic: first line or after "Name:")
    lines = cv_content.split('\n')
    for i, line in enumerate(lines[:10]):  # Check first 10 lines
        line_clean = line.strip()
        if line_clean and len(line_clean.split()) <= 4 and len(line_clean) < 50:
            # Skip lines with obvious non-name content
            if not any(char in line_clean.lower() for char in ['@', 'http', ':', 'phone', 'email', 'address']):
                # Check if it looks like a name (contains letters, reasonable length)
                if re.match(r'^[A-Za-z\s\-\.\']+$', line_clean) and len(line_clean) > 3:
                    contact_info['name'] = line_clean
                    break
    
    # Extract location
    location_keywords = ['location', 'address', 'city', 'state', 'country']
    location_patterns = [
        r'((?:[A-Z][a-z]+,?\s*){1,3}(?:CA|NY|TX|FL|WA|IL|PA|OH|GA|NC|MI|NJ|VA|MA|IN|TN|AZ|MD|MO|WI|CO|MN|LA|AL|KY|SC|OK|IA|AR|UT|NV|KS|NM|WV|NE|ID|HI|ME|MT|RI|DE|SD|ND|AK|VT|WY|DC))',
        r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, State
        r'([A-Z][a-z]+\s*,\s*[A-Z]{2})',  # City, ST
    ]
    
    for pattern in location_patterns:
        location_match = re.search(pattern, cv_content)
        if location_match:
            contact_info['location'] = location_match.group(1)
            break
    
    return contact_info


def analyze_bonus_skills(cv_content: str, job_profile) -> Dict[str, float]:
    """Analyze bonus skills not in the core requirements"""
    cv_lower = cv_content.lower()
    
    # Get required skill names
    required_skills = [skill.name.lower() for skill in job_profile.required_skills]
    
    # Define comprehensive bonus skills by category
    bonus_skill_categories = {
        'Leadership': ['leadership', 'team lead', 'mentoring', 'coaching', 'project management'],
        'Communication': ['presentation', 'public speaking', 'documentation', 'technical writing'],
        'Certifications': ['certified', 'certification', 'aws certified', 'google certified', 'microsoft certified'],
        'Languages': ['bilingual', 'multilingual', 'spanish', 'french', 'german', 'mandarin'],
        'Industry Knowledge': ['domain expertise', 'industry experience', 'business knowledge'],
        'Soft Skills': ['problem solving', 'analytical thinking', 'creative', 'innovation'],
        'Tools & Platforms': ['jira', 'confluence', 'slack', 'figma', 'adobe', 'microsoft office'],
        'Methodologies': ['agile', 'scrum', 'lean', 'six sigma', 'design thinking']
    }
    
    bonus_scores = {}
    
    for category, skills in bonus_skill_categories.items():
        category_score = 0.0
        found_skills = []
        
        for skill in skills:
            if skill in cv_lower and skill not in required_skills:
                category_score += 0.1
                found_skills.append(skill)
        
        if category_score > 0:
            bonus_scores[category] = min(category_score, 0.5)  # Cap at 0.5
    
    return bonus_scores


def get_candidate_details(cv_content: str) -> Dict[str, any]:
    """
    Extract comprehensive candidate details with enhanced accuracy
    """
    contact_info = extract_candidate_contact_info(cv_content)
    
    # Enhanced career highlights extraction
    career_highlights = extract_career_highlights(cv_content)
    
    # Calculate experience with enhanced precision
    experience_years = calculate_years_of_experience(cv_content)
    
    # Extract top skills with evidence
    top_skills = extract_top_skills_with_evidence(cv_content)
    
    return {
        'contact_info': contact_info,
        'career_highlights': career_highlights,
        'experience_years': experience_years,
        'top_skills': top_skills
    }


def extract_career_highlights(cv_content: str) -> List[str]:
    """Extract key career highlights and achievements"""
    highlights = []
    
    # Achievement patterns with quantifiable results
    achievement_patterns = [
        r'(increased|improved|reduced|achieved|delivered|led|managed|built|developed|created)[^.!?]*(\d+[\%\+\-\$]|x\d+|\d+x)[^.!?]*[.!?]',
        r'(successfully|effectively)[^.!?]*[.!?]',
        r'(award|recognition|promotion|certified)[^.!?]*[.!?]',
        r'(responsible for|led team of|managed)[^.!?]*[.!?]'
    ]
    
    for pattern in achievement_patterns:
        matches = re.finditer(pattern, cv_content, re.IGNORECASE)
        for match in matches:
            highlight = match.group(0).strip()
            if 20 < len(highlight) < 150 and highlight not in highlights:
                highlights.append(highlight)
                if len(highlights) >= 5:
                    break
        if len(highlights) >= 5:
            break
    
    return highlights[:5]


def extract_top_skills_with_evidence(cv_content: str) -> List[Dict[str, str]]:
    """Extract top skills with supporting evidence"""
    cv_lower = cv_content.lower()
    
    # Common technical skills to look for
    skill_patterns = {
        'Python': ['python', 'django', 'flask', 'fastapi', 'pandas'],
        'JavaScript': ['javascript', 'js', 'react', 'node.js', 'vue', 'angular'],
        'Data Analysis': ['data analysis', 'analytics', 'sql', 'excel', 'tableau'],
        'Project Management': ['project management', 'scrum', 'agile', 'jira'],
        'Cloud Computing': ['aws', 'azure', 'gcp', 'cloud', 'docker'],
        'Machine Learning': ['machine learning', 'ml', 'ai', 'tensorflow', 'pytorch'],
        'Database': ['mysql', 'postgresql', 'mongodb', 'database'],
        'API Development': ['api', 'rest', 'restful', 'microservices'],
        'Frontend Development': ['frontend', 'html', 'css', 'responsive'],
        'Backend Development': ['backend', 'server', 'api', 'database']
    }
    
    skills_with_evidence = []
    
    for skill_name, patterns in skill_patterns.items():
        evidence_count = 0
        skill_evidence = []
        
        for pattern in patterns:
            if pattern in cv_lower:
                evidence_count += 1
                # Find context for this pattern
                context_pattern = r'[^.!?]*' + re.escape(pattern) + r'[^.!?]*[.!?]?'
                matches = re.findall(context_pattern, cv_content, re.IGNORECASE)
                for match in matches[:2]:  # Top 2 matches
                    clean_match = match.strip()[:100]
                    if clean_match and clean_match not in skill_evidence:
                        skill_evidence.append(clean_match)
        
        if evidence_count > 0:
            skills_with_evidence.append({
                'skill': skill_name,
                'evidence_count': evidence_count,
                'evidence': skill_evidence[:2]  # Top 2 pieces of evidence
            })
    
    # Sort by evidence count and return top skills
    skills_with_evidence.sort(key=lambda x: x['evidence_count'], reverse=True)
    return skills_with_evidence[:6]  # Top 6 skills
    """Extract years of experience from CV content"""
    # Look for experience patterns
    experience_patterns = [
        r'(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\s*years?\s+(?:of\s+)?(?:professional\s+)?experience',
        r'experience.*?(\d+)\s*years?',
        r'(\d+)\s*years?\s+in\s+(?:software|development|programming)'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, cv_content.lower())
        if matches:
            return float(matches[0])
    
    # Calculate based on work history dates
    year_pattern = r'(20\d{2})\s*[-–]\s*(20\d{2}|present|current)'
    date_matches = re.findall(year_pattern, cv_content.lower())
    
    if date_matches:
        total_years = 0
        current_year = 2025
        
        for start_year, end_year in date_matches:
            start = int(start_year)
            end = current_year if end_year in ['present', 'current'] else int(end_year)
            total_years += max(0, end - start)
        
        return float(total_years)
    
    # Fallback: estimate based on education graduation and current year
    grad_pattern = r'(20\d{2})'
    grad_matches = re.findall(grad_pattern, cv_content)
    if grad_matches:
        latest_year = max(int(year) for year in grad_matches)
        estimated_years = max(0, 2025 - latest_year - 1)  # Assume 1 year delay after graduation
        return float(min(estimated_years, 15))  # Cap at 15 years
    
    return 2.0  # Default assumption
    """Extract years of experience from CV content"""
    # Look for experience patterns
    experience_patterns = [
        r'(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\s*years?\s+(?:of\s+)?(?:professional\s+)?experience',
        r'experience.*?(\d+)\s*years?',
        r'(\d+)\s*years?\s+in\s+(?:software|development|programming)'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, cv_content.lower())
        if matches:
            return float(matches[0])
    
    # Calculate based on work history dates
    year_pattern = r'(20\d{2})\s*[-–]\s*(20\d{2}|present|current)'
    date_matches = re.findall(year_pattern, cv_content.lower())
    
    if date_matches:
        total_years = 0
        current_year = 2025
        
        for start_year, end_year in date_matches:
            start = int(start_year)
            end = current_year if end_year in ['present', 'current'] else int(end_year)
            total_years += max(0, end - start)
        
        return min(total_years, 20)  # Cap at 20 years
    
    # Default estimation based on content complexity
    content_length = len(cv_content)
    if content_length > 3000:
        return 5.0
    elif content_length > 2000:
        return 3.0
    else:
        return 2.0

def extract_candidate_details(cv_content: str, original_filename: str) -> Dict:
    """Extract candidate personal details, contact info, and links from CV"""
    import re
    
    cv_lines = cv_content.split('\n')
    details = {
        'name': None,
        'email': None,
        'phone': None,
        'location': None,
        'linkedin': None,
        'github': None,
        'portfolio': None,
        'other_links': []
    }
    
    # Extract name (usually in first few lines, often the largest text or first line)
    for i, line in enumerate(cv_lines[:5]):
        line_clean = line.strip()
        if line_clean and len(line_clean) > 3:
            # Skip common CV headers
            if not any(header in line_clean.lower() for header in ['resume', 'cv', 'curriculum', 'vitae', 'experience', 'education', 'skills']):
                # Look for name patterns (2-4 words, proper capitalization)
                words = line_clean.split()
                if 2 <= len(words) <= 4 and all(word[0].isupper() if word.isalpha() else True for word in words):
                    details['name'] = line_clean
                    break
    
    # If no name found, try to extract from filename
    if not details['name']:
        filename_clean = original_filename.replace('.txt', '').replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        words = filename_clean.split()
        # Look for name-like patterns in filename
        if 2 <= len(words) <= 4:
            details['name'] = ' '.join(word.capitalize() for word in words if not word.lower() in ['cv', 'resume'])
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, cv_content)
    if emails:
        details['email'] = emails[0]  # Take the first email found
    
    # Extract phone numbers (various formats)
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International format
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\+?\d{10,15}',  # Simple international
        r'\d{3}-\d{3}-\d{4}',  # Dash format
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, cv_content)
        if phones:
            details['phone'] = phones[0]
            break
    
    # Extract location (look for city, state, country patterns)
    location_patterns = [
        r'(?:Location|Address|City):\s*([^\n]+)',
        r'([A-Z][a-z]+,\s*[A-Z]{2}(?:\s+\d{5})?)',  # City, State format
        r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country format
    ]
    
    for pattern in location_patterns:
        locations = re.findall(pattern, cv_content, re.IGNORECASE)
        if locations:
            details['location'] = locations[0].strip()
            break
    
    # Extract LinkedIn profiles
    linkedin_patterns = [
        r'linkedin\.com/in/([^\s\n]+)',
        r'linkedin\.com/profile/([^\s\n]+)',
        r'(https?://(?:www\.)?linkedin\.com/in/[^\s\n]+)',
    ]
    
    for pattern in linkedin_patterns:
        linkedin_matches = re.findall(pattern, cv_content, re.IGNORECASE)
        if linkedin_matches:
            linkedin_url = linkedin_matches[0]
            if not linkedin_url.startswith('http'):
                linkedin_url = f"https://linkedin.com/in/{linkedin_url}"
            details['linkedin'] = linkedin_url
            break
    
    # Extract GitHub profiles
    github_patterns = [
        r'github\.com/([^\s\n]+)',
        r'(https?://(?:www\.)?github\.com/[^\s\n]+)',
    ]
    
    for pattern in github_patterns:
        github_matches = re.findall(pattern, cv_content, re.IGNORECASE)
        if github_matches:
            github_url = github_matches[0]
            if not github_url.startswith('http'):
                github_url = f"https://github.com/{github_url}"
            details['github'] = github_url
            break
    
    # Extract portfolio websites and other links
    url_pattern = r'https?://(?:www\.)?([^\s\n]+\.[a-z]{2,}(?:/[^\s\n]*)?)'
    urls = re.findall(url_pattern, cv_content, re.IGNORECASE)
    
    portfolio_keywords = ['portfolio', 'website', 'site', 'project', 'demo', 'work']
    
    for url in urls:
        full_url = f"https://{url}" if not url.startswith('http') else url
        
        # Skip already captured LinkedIn/GitHub
        if 'linkedin.com' in url or 'github.com' in url:
            continue
            
        # Check if this looks like a portfolio
        if any(keyword in url.lower() for keyword in portfolio_keywords):
            if not details['portfolio']:
                details['portfolio'] = full_url
        else:
            # Add to other links if it's not already captured
            if full_url not in details['other_links']:
                details['other_links'].append(full_url)
    
    # Look for portfolio in text context
    if not details['portfolio']:
        portfolio_text_patterns = [
            r'(?:Portfolio|Website|Personal site):\s*(https?://[^\s\n]+)',
            r'(?:Check out my work at|View my portfolio at):\s*(https?://[^\s\n]+)',
        ]
        
        for pattern in portfolio_text_patterns:
            portfolio_matches = re.findall(pattern, cv_content, re.IGNORECASE)
            if portfolio_matches:
                details['portfolio'] = portfolio_matches[0]
                break
    
    # Extract project URLs and demo links from project descriptions
    project_patterns = [
        r'(?:Live demo|Demo|Project URL|Site|Link):\s*(https?://[^\s\n]+)',
        r'(?:Built|Created|Developed)\s+.*?(?:at|@)\s*(https?://[^\s\n]+)',
    ]
    
    for pattern in project_patterns:
        project_urls = re.findall(pattern, cv_content, re.IGNORECASE)
        for url in project_urls:
            if url not in details['other_links'] and url != details['portfolio']:
                details['other_links'].append(url)
    
    return details

def mock_ai_analysis(job_profile: JobProfile, cv_content: str, candidate_id: str, original_filename: str) -> CandidateResult:
    """
    Enhanced CV analysis with recruiter-friendly, evidence-based evaluation
    """
    
    # Extract detailed candidate information first
    candidate_details = extract_candidate_details(cv_content, original_filename)
    
    # Get candidate name for personalization
    candidate_name = candidate_details.get("name", original_filename.replace('.txt', '').replace('_', ' ').title())
    
    # Analyze each skill thoroughly
    skill_matches = []
    for skill in job_profile.required_skills:
        match_score, evidence = analyze_skill_match(skill.name, cv_content)
        skill_matches.append({
            "name": skill.name,
            "match": match_score,
            "weight": skill.weight,
            "evidence": evidence
        })
    
    # Calculate realistic years of experience
    years_experience = calculate_years_of_experience(cv_content)
    
    # Extract concrete achievements and career highlights
    career_highlights = extract_career_highlights(cv_content)
    
    # Calculate weighted fit score with more realistic scaling
    weighted_score = sum(sm["match"] * sm["weight"] for sm in skill_matches)
    total_weight = sum(sm["weight"] for sm in skill_matches)
    base_score = (weighted_score / total_weight) * 10 if total_weight > 0 else 0
    
    # Apply realistic scoring adjustments
    fit_score = apply_realistic_scoring_adjustments(base_score, years_experience, cv_content)
    
    # Determine experience level for proper role suggestions
    if years_experience >= 7:
        experience_level = "senior"
    elif years_experience >= 3:
        experience_level = "mid-level"
    elif years_experience >= 1:
        experience_level = "junior"
    else:
        experience_level = "entry-level"
    
    # Generate intelligent role suggestions based on actual CV content
    suggested_roles = generate_suggested_roles(job_profile, skill_matches, years_experience, fit_score)
    
    # Build comprehensive analysis
    why = []
    
    # Professional header with candidate name
    header = f"📄 **Candidate Analysis: {candidate_name} – {job_profile.title}**"
    why.append(header)
    
    # Executive Summary
    summary = build_executive_summary(skill_matches, years_experience, cv_content, fit_score)
    why.append(summary)
    
    # Career Highlights section
    if career_highlights:
        why.append("**🏆 Career Highlights**")
        for highlight in career_highlights[:3]:
            why.append(f"• {highlight}")
        why.append("")
    
    # Skills Analysis with concrete evidence
    why.append("**🔧 Skills Assessment**\n")
    skills_analysis = build_evidence_based_skills_analysis(skill_matches, cv_content)
    why.extend(skills_analysis)
    
    # Balanced Pros section with specific strengths
    pros_section = build_specific_pros_section(skill_matches, cv_content, years_experience)
    why.extend(pros_section)
    
    # Expanded Cons section showing clear gaps
    cons_section = build_realistic_cons_section(skill_matches, cv_content, job_profile)
    why.extend(cons_section)
    
    # Realistic final assessment
    final_assessment = build_realistic_final_assessment(fit_score, pros_section, cons_section)
    why.extend(final_assessment)
    
    # Alternative role suggestions
    why.append("**🔄 Alternative Role Considerations**")
    for i, role in enumerate(suggested_roles[:3], 1):
        why.append(f"{i}. {role} - Based on demonstrated skills and experience level")
    
    # Build skill analysis for detailed breakdown
    skill_analysis = {}
    for skill_match in skill_matches:
        skill_analysis[skill_match["name"]] = {
            "score": min(skill_match["match"] * 10, 10),
            "evidence": skill_match["evidence"][:3],
            "years_experience": 0.0  # Placeholder for individual skill experience
        }
    
    # Generate concise CV summary
    cv_summary = f"**{candidate_name}** - {experience_level.title()} {extract_primary_domain(cv_content)} candidate with {years_experience:.0f} years of professional experience. **Strong in:** {get_top_skills(skill_matches, 2)}. {get_fit_assessment_phrase(fit_score)} ({fit_score:.1f}/10) for this position."
    
    # Enhanced red flags detection
    red_flags = []
    # Find significant skill gaps
    critical_gaps = [sm["name"] for sm in skill_matches if sm["match"] < 0.3 and sm["weight"] >= 0.8]
    if critical_gaps:
        red_flags.append(f"Critical skill gaps in {', '.join(critical_gaps[:2])}")
    
    # Experience vs role mismatch
    if 'senior' in job_profile.title.lower() and years_experience < 4:
        red_flags.append("Experience level below typical senior role requirements")
    
    return CandidateResult(
        candidate_id=candidate_id,
        file_name=original_filename,
        fit_score=fit_score,
        why=why,
        cv_summary=cv_summary,
        suggested_roles=suggested_roles,
        red_flags=red_flags,
        years_experience=years_experience,
        last_role=extract_last_role(cv_content),
        candidate_details=candidate_details,
        skill_analysis=skill_analysis
    )


def generate_suggested_roles(job_profile: JobProfile, skill_matches: List[Dict], years_experience: float, fit_score: float) -> List[str]:
    """
    Generate intelligent role suggestions based on skills and experience
    """
    suggested_roles = []
    
    # Primary role suggestion based on fit
    if fit_score >= 7:
        suggested_roles.append(job_profile.title)
    elif fit_score >= 5:
        suggested_roles.append(f"Junior {job_profile.title}")
    else:
        suggested_roles.append(f"Entry-level {job_profile.title}")
    
    # Get top skills for role suggestions
    top_skills = [sm["name"].lower() for sm in skill_matches if sm["match"] > 0.5]
    
    # Dynamic role suggestions based on skills
    role_mappings = {
        'javascript': ['Frontend Developer', 'Full Stack Developer', 'Web Developer'],
        'react': ['React Developer', 'Frontend Developer', 'UI Developer'],
        'python': ['Python Developer', 'Backend Developer', 'Data Analyst'],
        'java': ['Java Developer', 'Backend Developer', 'Enterprise Developer'],
        'angular': ['Angular Developer', 'Frontend Developer', 'SPA Developer'],
        'vue': ['Vue.js Developer', 'Frontend Developer', 'Web Developer'],
        'node': ['Node.js Developer', 'Backend Developer', 'API Developer'],
        'php': ['PHP Developer', 'Web Developer', 'Backend Developer'],
        'c#': ['C# Developer', '.NET Developer', 'Backend Developer'],
        'sql': ['Database Developer', 'Data Analyst', 'Backend Developer'],
        'aws': ['Cloud Engineer', 'DevOps Engineer', 'Infrastructure Engineer'],
        'docker': ['DevOps Engineer', 'Site Reliability Engineer', 'Platform Engineer'],
        'kubernetes': ['DevOps Engineer', 'Cloud Architect', 'Platform Engineer'],
        'machine learning': ['ML Engineer', 'Data Scientist', 'AI Developer'],
        'data science': ['Data Scientist', 'Data Analyst', 'Research Analyst'],
        'shopify': ['Shopify Developer', 'E-commerce Developer', 'Theme Developer'],
        'wordpress': ['WordPress Developer', 'CMS Developer', 'Web Developer'],
        'salesforce': ['Salesforce Developer', 'CRM Developer', 'Business Analyst'],
        'mobile': ['Mobile Developer', 'App Developer', 'iOS/Android Developer'],
        'ios': ['iOS Developer', 'Mobile Developer', 'Swift Developer'],
        'android': ['Android Developer', 'Mobile Developer', 'Kotlin Developer'],
        'react native': ['React Native Developer', 'Mobile Developer', 'Cross-platform Developer'],
        'flutter': ['Flutter Developer', 'Mobile Developer', 'Dart Developer'],
        'ui': ['UI Developer', 'Frontend Developer', 'Design Systems Developer'],
        'ux': ['UX Developer', 'Frontend Developer', 'Product Developer'],
        'testing': ['QA Engineer', 'Test Automation Engineer', 'Quality Assurance'],
        'api': ['API Developer', 'Backend Developer', 'Integration Developer'],
        'blockchain': ['Blockchain Developer', 'Smart Contract Developer', 'Web3 Developer'],
        'cybersecurity': ['Security Engineer', 'Cybersecurity Analyst', 'InfoSec Specialist']
    }
    
    # Add role suggestions based on top skills
    skill_based_roles = set()
    for skill in top_skills:
        for key, roles in role_mappings.items():
            if key in skill or skill in key:
                skill_based_roles.update(roles)
    
    # Add relevant roles to suggestions
    for role in list(skill_based_roles)[:3]:  # Limit to 3 additional roles
        if role not in suggested_roles and role != job_profile.title:
            suggested_roles.append(role)
    
    # Experience-based role adjustments
    if years_experience >= 5:
        senior_roles = [f"Senior {role}" for role in suggested_roles[:2] if not role.startswith('Senior')]
        suggested_roles.extend(senior_roles[:2])
    elif years_experience >= 8:
        lead_roles = [f"Lead {role}" for role in suggested_roles[:1] if not role.startswith('Lead')]
        suggested_roles.extend(lead_roles[:1])
    
    # Ensure we have enough suggestions
    if len(suggested_roles) < 3:
        generic_roles = ['Software Developer', 'Technical Specialist', 'IT Professional']
        for role in generic_roles:
            if role not in suggested_roles:
                suggested_roles.append(role)
                if len(suggested_roles) >= 3:
                    break
    
    return suggested_roles[:4]  # Return max 4 suggestions


def extract_career_highlights(cv_content: str) -> List[str]:
    """Extract concrete achievements and career highlights from CV"""
    highlights = []
    cv_lower = cv_content.lower()
    
    # Patterns for achievements with quantifiable results
    achievement_patterns = [
        r'(\w+ed|built|created|led|managed|increased|reduced|improved|achieved|delivered|generated)[^.!?]*(\d+%|\$\d+|\d+[km]?\+)[^.!?]*[.!?]',
        r'(won|awarded|recognized|featured|speaker|published|certified)[^.!?]*[.!?]',
        r'(\d+% increase|\d+% improvement|\d+% reduction|saved \$\d+|generated \$\d+)[^.!?]*[.!?]'
    ]
    
    for pattern in achievement_patterns:
        matches = re.findall(pattern, cv_content, re.IGNORECASE)
        for match in matches[:3]:
            if isinstance(match, tuple):
                full_match = ' '.join(match)
            else:
                full_match = match
            
            # Clean up the highlight
            clean_highlight = full_match.strip().replace('\n', ' ').replace('  ', ' ')
            if len(clean_highlight) > 20 and clean_highlight not in highlights:
                highlights.append(clean_highlight[:150] + "..." if len(clean_highlight) > 150 else clean_highlight)
    
    # If no quantifiable achievements found, extract key accomplishments
    if not highlights:
        lines = cv_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                clean_line = line[1:].strip()
                if any(word in clean_line.lower() for word in ['led', 'managed', 'built', 'created', 'developed', 'designed']):
                    if len(clean_line) > 30:
                        highlights.append(clean_line[:120] + "..." if len(clean_line) > 120 else clean_line)
                        if len(highlights) >= 3:
                            break
    
    return highlights[:3]


def apply_realistic_scoring_adjustments(base_score: float, years_experience: float, cv_content: str) -> float:
    """Apply realistic adjustments to prevent inflated scores"""
    adjusted_score = base_score
    
    # Experience level adjustment
    if years_experience < 2 and base_score > 8:
        adjusted_score = min(base_score, 7.5)  # Cap junior candidates
    elif years_experience < 5 and base_score > 9:
        adjusted_score = min(base_score, 8.5)  # Cap mid-level candidates
    
    # Check for red flags that should lower score
    cv_lower = cv_content.lower()
    if any(flag in cv_lower for flag in ['gap', 'unemployed', 'seeking', 'looking for']):
        adjusted_score = max(adjusted_score - 0.5, 0)
    
    # Ensure minimum realistic variance (not everyone gets 9-10)
    if adjusted_score > 9.5:
        adjusted_score = 9.5  # Very rare perfect matches
    
    return round(adjusted_score, 1)


def build_executive_summary(skill_matches: List[Dict], years_experience: float, cv_content: str, fit_score: float) -> str:
    """Build a concise executive summary"""
    # Categorize skills by strength
    strong_skills = [sm["name"] for sm in skill_matches if sm["match"] > 0.65]
    weak_skills = [sm["name"] for sm in skill_matches if sm["match"] < 0.4]
    
    # Experience level
    if years_experience >= 7:
        exp_level = "Senior-level professional"
    elif years_experience >= 4:
        exp_level = "Mid-level professional"
    elif years_experience >= 2:
        exp_level = "Junior professional"
    else:
        exp_level = "Entry-level candidate"
    
    summary = f"**📋 Executive Summary**\n"
    summary += f"{exp_level} with {years_experience:.0f} years of experience. "
    
    if strong_skills:
        summary += f"Strengths: {', '.join(strong_skills[:3])}. "
    
    if weak_skills and len(weak_skills) > 1:
        summary += f"Development areas: {', '.join(weak_skills[:2])}. "
    
    # Overall assessment
    if fit_score >= 8.5:
        summary += "Excellent fit for this role."
    elif fit_score >= 7:
        summary += "Strong candidate with minor gaps."
    elif fit_score >= 5.5:
        summary += "Solid potential with some development needed."
    else:
        summary += "Limited fit - significant skill gaps present."
    
    return summary


def build_evidence_based_skills_analysis(skill_matches: List[Dict], cv_content: str) -> List[str]:
    """Build detailed skills analysis with concrete evidence"""
    analysis = []
    
    for skill_match in skill_matches:
        skill_score = skill_match["match"] * 10
        
        # More conservative rating thresholds
        if skill_score >= 8.5:
            rating_desc = "Excellent"
            color_class = "text-green-700"
        elif skill_score >= 7:
            rating_desc = "Strong"
            color_class = "text-green-600"
        elif skill_score >= 5:
            rating_desc = "Adequate"
            color_class = "text-orange-500"
        elif skill_score >= 3:
            rating_desc = "Developing"
            color_class = "text-orange-600"
        else:
            rating_desc = "Insufficient"
            color_class = "text-red-600"
        
        # Create skill header with rating
        skill_header = f"**{skill_match['name']}** – <span class='{color_class} font-bold'>{rating_desc} ({skill_score:.1f}/10)</span>"
        analysis.append(skill_header)
        
        # Add concrete evidence with context
        evidence_added = 0
        if skill_match["evidence"] and len(skill_match["evidence"]) > 0:
            for evidence in skill_match["evidence"][:2]:  # Limit to 2 pieces of evidence
                if evidence and not evidence.startswith("Limited evidence") and len(evidence.strip()) > 20:
                    clean_evidence = evidence.replace("...", "").strip()
                    if len(clean_evidence) > 80:
                        clean_evidence = clean_evidence[:80] + "..."
                    analysis.append(f"  • Evidence: {clean_evidence}")
                    evidence_added += 1
        
        if evidence_added == 0:
            analysis.append(f"  • Evidence: No clear demonstration found in CV")
        
        analysis.append("")  # Add spacing
    
    return analysis


def build_specific_pros_section(skill_matches: List[Dict], cv_content: str, years_experience: float) -> List[str]:
    """Build specific pros highlighting unique candidate strengths"""
    pros = ["**✅ Key Strengths**"]
    
    # Find genuinely strong skills (higher threshold)
    strong_skills = [sm for sm in skill_matches if sm["match"] > 0.7]
    
    # Experience-based strengths
    if years_experience >= 7:
        pros.append(f"• Senior Expertise: {years_experience:.0f} years of proven industry experience")
    elif years_experience >= 4:
        pros.append(f"• Solid Experience: {years_experience:.0f} years with demonstrated growth trajectory")
    elif years_experience >= 2:
        pros.append(f"• Practical Experience: {years_experience:.0f} years of hands-on application")
    
    # Strong skill areas
    if strong_skills:
        top_skill = strong_skills[0]
        pros.append(f"• {top_skill['name']} Proficiency: Demonstrated strong capability with practical application")
    
    # Look for leadership indicators
    cv_lower = cv_content.lower()
    if any(word in cv_lower for word in ['led team', 'managed', 'mentored', 'supervised']):
        pros.append("• Leadership Experience: Proven ability to guide teams and manage responsibilities")
    
    # Look for quantifiable achievements
    if any(char in cv_content for char in ['%', '$']) and any(word in cv_lower for word in ['increased', 'improved', 'reduced', 'achieved']):
        pros.append("• Results-Oriented: Track record of delivering measurable business impact")
    
    # Ensure we have at least 2-3 meaningful pros
    if len(pros) < 3:
        pros.append("• Growth Potential: Demonstrates learning ability and adaptability")
    
    return pros


def build_realistic_cons_section(skill_matches: List[Dict], cv_content: str, job_profile: JobProfile) -> List[str]:
    """Build realistic cons section showing clear development areas"""
    cons = ["**⚠️ Development Areas**"]
    
    # Find significant skill gaps
    weak_skills = [sm for sm in skill_matches if sm["match"] < 0.4 and sm["weight"] >= 0.6]
    moderate_skills = [sm for sm in skill_matches if 0.4 <= sm["match"] < 0.65 and sm["weight"] >= 0.7]
    
    # Critical skill gaps
    if weak_skills:
        skill_names = [s['name'] for s in weak_skills[:2]]
        cons.append(f"• Skill Gaps: Limited demonstration of {', '.join(skill_names)}")
    
    # Areas needing development
    if moderate_skills:
        skill_names = [s['name'] for s in moderate_skills[:2]]
        cons.append(f"• Development Needed: Moderate experience in {', '.join(skill_names)} - requires strengthening")
    
    # Experience level considerations
    years_exp = calculate_years_of_experience(cv_content)
    if years_exp < 2:
        cons.append("• Limited Experience: May require additional mentoring and extended onboarding period")
    
    # Seniority misalignment
    job_title_lower = job_profile.title.lower()
    if 'senior' in job_title_lower and years_exp < 5:
        cons.append("• Seniority Gap: Experience level may not align with senior-level expectations")
    
    # Technical depth concerns
    high_skill_count = len([s for s in skill_matches if s["match"] > 0.7])
    if 'senior' in job_title_lower and high_skill_count < 2:
        cons.append("• Technical Depth: May need time to develop deep expertise in core competencies")
    
    # Look for potential concerns in CV
    cv_lower = cv_content.lower()
    if 'career change' in cv_lower or 'transition' in cv_lower:
        cons.append("• Career Transition: Adapting skills from different domain may require adjustment period")
    
    # Ensure we have realistic cons (not just token ones)
    if len(cons) == 1:  # Only header
        cons.append("• Standard Considerations: Typical onboarding and skill refinement expected for role requirements")
    
    return cons


def build_realistic_final_assessment(fit_score: float, pros_section: List[str], cons_section: List[str]) -> List[str]:
    """Build realistic final assessment based on analysis"""
    assessment = []
    
    # More conservative score interpretation
    if fit_score >= 8.5:
        rating_text = "Excellent Match"
        recommendation = "Strong hire - minimal risk, quick onboarding expected"
    elif fit_score >= 7.5:
        rating_text = "Very Good Match"
        recommendation = "Recommended hire with standard onboarding process"
    elif fit_score >= 6.5:
        rating_text = "Good Match"
        recommendation = "Solid candidate - plan for targeted skill development"
    elif fit_score >= 5.5:
        rating_text = "Moderate Match"
        recommendation = "Consider if team can provide necessary development support"
    else:
        rating_text = "Limited Match"
        recommendation = "Significant investment required - evaluate alternative roles"
    
    assessment.append(f"**🎯 Hiring Recommendation: {rating_text} ({fit_score:.1f}/10)**")
    assessment.append(f"Decision: {recommendation}")
    
    # Realistic timeline based on gaps
    pros_count = len([p for p in pros_section if p.startswith("•")])
    cons_count = len([c for c in cons_section if c.startswith("•")])
    
    if fit_score >= 8:
        assessment.append("Onboarding: 2-4 weeks to full productivity")
    elif fit_score >= 6.5:
        assessment.append("Onboarding: 6-8 weeks with focused training plan")
    else:
        assessment.append("Onboarding: 3-4 months comprehensive development program required")
    
    return assessment


def extract_primary_domain(cv_content: str) -> str:
    """Extract primary domain/field from CV content"""
    cv_lower = cv_content.lower()
    
    if any(word in cv_lower for word in ['data scientist', 'machine learning', 'analytics', 'ml engineer']):
        return "data science"
    elif any(word in cv_lower for word in ['software', 'developer', 'engineer', 'programming']):
        return "software development"
    elif any(word in cv_lower for word in ['designer', 'ux', 'ui', 'design']):
        return "design"
    elif any(word in cv_lower for word in ['devops', 'infrastructure', 'cloud', 'systems']):
        return "devops/infrastructure"
    elif any(word in cv_lower for word in ['product manager', 'pm', 'product']):
        return "product management"
    elif any(word in cv_lower for word in ['sales', 'business development', 'account']):
        return "sales"
    else:
        return "professional"


def get_top_skills(skill_matches: List[Dict], count: int = 2) -> str:
    """Get top performing skills as comma-separated string"""
    top_skills = sorted(skill_matches, key=lambda x: x["match"], reverse=True)[:count]
    return ", ".join([skill["name"] for skill in top_skills if skill["match"] > 0.5])


def get_fit_assessment_phrase(fit_score: float) -> str:
    """Get appropriate fit assessment phrase"""
    if fit_score >= 8.5:
        return "**Excellent match**"
    elif fit_score >= 7:
        return "**Strong fit**"
    elif fit_score >= 5.5:
        return "**Good potential**"
    else:
        return "**Moderate fit**"


def extract_last_role(cv_content: str) -> str:
    """Extract the most recent role from CV"""
    lines = cv_content.split('\n')
    for line in lines:
        line = line.strip()
        if any(word in line.lower() for word in ['current', 'present', '2024', '2025']) and \
           any(word in line.lower() for word in ['engineer', 'manager', 'analyst', 'designer', 'developer', 'specialist']):
            return line[:50] + "..." if len(line) > 50 else line
    return "Not clearly specified"
