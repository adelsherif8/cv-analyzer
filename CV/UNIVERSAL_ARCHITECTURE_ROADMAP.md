# Universal CV Analyzer Architecture - Migration Roadmap

## Current State Assessment ✅

Your existing `cv_analyzer_agent.py` already implements many universal principles:

- **Section-aware scoring** (Experience 1.0 → Skills 0.7 → Certs 0.4)
- **Evidence-based rating** with quality factors (tools, metrics, recency)
- **Fuzzy matching** for variant spellings (RapidFuzz 86% threshold)
- **Role block parsing** for real tenure/recency calculation
- **Score calibration** for realistic ranges
- **Evidence deduplication** to prevent cross-skill leakage

**Migration Effort: ~70% already done!** 🎉

## Phase 1: Vector Skill Ontology (2-3 days)

### Replace hand-coded aliases with universal skill graph

```python
# Current approach (limited scope)
SKILL_ALIAS_MAP = {
    "react.js development": ["react", "reactjs", "jsx"],
    # ... 14 hard-coded skills
}

# Universal approach
class SkillOntology:
    def __init__(self):
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
        self.skill_index = {}  # skill_id -> metadata
        self.vector_index = None  # FAISS index
        self.alias_index = {}  # fuzzy lookup
    
    def nearest_skills(self, phrase: str, k=8, cos_thresh=0.78, fuzz_thresh=86):
        # Vector search + fuzzy fallback
        pass
```

### Seed with open datasets

1. **ESCO Skills** (free EU taxonomy, 30k+ skills)
2. **O*NET Database** (US occupational data)
3. **StackOverflow Tags** (tech skills)
4. **Industry standards** (healthcare: SNOMED, finance: IFRS, etc.)

### Implementation steps

```bash
# Install dependencies
pip install sentence-transformers faiss-cpu datasets

# Download ESCO dataset
wget https://ec.europa.eu/esco/api/resource/downloads/v1.1.1/skills.csv

# Build initial ontology
python scripts/build_skill_ontology.py
```

## Phase 2: Auto JD Understanding (1 week)

### Extract skills from any job description

```python
class JDExtractor:
    def extract_requirements(self, jd_text: str) -> List[SkillWeight]:
        # 1. NER + noun phrase extraction
        chunks = self.extract_noun_phrases(jd_text)
        
        # 2. Map to skill ontology
        skills = []
        for chunk in chunks:
            matches = self.ontology.nearest_skills(chunk)
            if matches:
                skills.append(matches[0])
        
        # 3. Derive weights from emphasis
        weights = self.derive_weights(jd_text, skills)
        
        # 4. Mark critical skills
        critical = self.detect_critical(jd_text, skills)
        
        return [SkillWeight(name=s, weight=w, critical=c) 
                for s, w, c in zip(skills, weights, critical)]
```

### Weight derivation heuristics

```python
def derive_weights(self, jd_text: str, skills: List[str]) -> List[float]:
    weights = []
    for skill in skills:
        weight = 0.1  # base
        
        # Section emphasis
        if self.in_requirements_section(jd_text, skill):
            weight += 0.3
        
        # Modifier words
        if self.has_emphasis_words(jd_text, skill, ["must", "required", "essential"]):
            weight += 0.4
        
        # Frequency & prominence
        count = jd_text.lower().count(skill.lower())
        weight += min(0.2, count * 0.05)
        
        weights.append(weight)
    
    # Softmax normalization
    return softmax(weights)
```

## Phase 3: Evidence Objects (1 week)

### Restructure evidence as rich objects

```python
@dataclass
class Evidence:
    skill_id: str
    sentence: str
    section: str
    role_block: Optional[RoleBlock]
    quality: EvidenceQuality
    similarity_score: float
    
@dataclass 
class EvidenceQuality:
    has_tools: bool
    has_metrics: bool
    action_verbs: List[str]
    section_weight: float
    recency_year: Optional[int]
    
    def compute_score(self) -> float:
        score = 0.0
        if self.has_tools: score += 0.4
        if self.has_metrics: score += 0.6
        if self.action_verbs: score += 0.3
        if self.recency_year and self.recency_year >= 2022: score += 0.25
        return score * (0.5 + self.section_weight)
```

### Enhanced evidence extraction

```python
def extract_cv_evidence(self, cv_text: str) -> List[Evidence]:
    evidence = []
    role_blocks = self._role_blocks(cv_text)
    
    for sentence, section_weight in self._sentences_with_section(cv_text):
        if self._is_skill_dump(sentence):
            continue
            
        # Map to nearest skills
        for skill_id, similarity in self.ontology.nearest_skills(sentence):
            if similarity >= 0.78:
                quality = self._assess_quality(sentence, section_weight)
                role_block = self._find_role_block(sentence, role_blocks)
                
                evidence.append(Evidence(
                    skill_id=skill_id,
                    sentence=sentence,
                    section=self._get_section_name(sentence),
                    role_block=role_block,
                    quality=quality,
                    similarity_score=similarity
                ))
    
    return self._deduplicate_evidence(evidence)
```

## Phase 4: Enhanced CV Parsing (1 week)

### Layout-aware document processing

```python
from unstructured.partition.auto import partition

class UniversalCVParser:
    def parse_document(self, file_path: str) -> ParsedCV:
        # Handle PDF/DOCX/HTML/TXT
        elements = partition(file_path)
        
        # Extract sections with layout context
        sections = self._extract_sections(elements)
        
        # OCR fallback for scanned documents
        if self._is_scanned(elements):
            ocr_text = self._ocr_extract(file_path)
            sections.update(self._parse_ocr_text(ocr_text))
        
        return ParsedCV(
            sections=sections,
            role_blocks=self._extract_role_blocks(elements),
            contact_info=self._extract_contact(elements),
            metadata=self._extract_metadata(elements)
        )
```

## Phase 5: Multilingual Support (1 week)

### Language detection & translation

```python
class MultilingualAnalyzer:
    def __init__(self):
        self.detector = fasttext.load_model('lid.176.bin')
        self.translators = {
            'es': MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-es-en'),
            'fr': MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-fr-en'),
            # ... more languages
        }
    
    def analyze_multilingual(self, cv_text: str, jd_text: str) -> AnalysisResult:
        cv_lang = self.detect_language(cv_text)
        jd_lang = self.detect_language(jd_text)
        
        # Translate to English for analysis
        cv_en = self.translate_if_needed(cv_text, cv_lang)
        jd_en = self.translate_if_needed(jd_text, jd_lang)
        
        # Analyze in English
        result = self.analyzer.analyze_candidate(cv_en, self.extract_jd(jd_en))
        
        # Translate results back if needed
        return self.localize_results(result, cv_lang)
```

## Phase 6: Calibration & Evaluation (ongoing)

### Cross-domain golden dataset

```python
# Collect 100+ JD-CV pairs across industries
golden_pairs = [
    {
        "jd": "Senior React Developer at FinTech...",
        "cv": "Frontend engineer with 5 years...",
        "human_score": 7.5,
        "human_label": "good",
        "domain": "technology"
    },
    {
        "jd": "Registered Nurse - ICU...",
        "cv": "Critical care nurse with CCRN...", 
        "human_score": 8.2,
        "human_label": "good",
        "domain": "healthcare"
    },
    # ... more across construction, legal, hospitality, etc.
]

# Fit calibration curve
from sklearn.isotonic import IsotonicRegression

calibrator = IsotonicRegression(out_of_bounds='clip')
calibrator.fit(raw_scores, human_scores)
```

## Implementation Priority

### Phase 1 - Quick Wins (This Week)
- [ ] Install sentence-transformers + FAISS
- [ ] Download ESCO skills dataset  
- [ ] Create basic `SkillOntology` class
- [ ] Replace 3-4 skills in `SKILL_ALIAS_MAP` with ontology lookup

### Phase 2 - Core Infrastructure (Next 2 Weeks)
- [ ] Full ontology integration
- [ ] Auto JD extraction
- [ ] Evidence objects
- [ ] Enhanced document parsing

### Phase 3 - Production Features (Month 2)
- [ ] Multilingual support
- [ ] Calibration system
- [ ] Continuous learning pipeline
- [ ] Bias & fairness guardrails

## Code Changes Required

### Minimal changes to existing code:

1. **Replace `get_aliases_for_skill()`**:
```python
# Before
aliases = self.get_aliases_for_skill(skill_name)

# After  
aliases = self.ontology.nearest_skills(skill_name, k=20)
```

2. **Enhance `extract_evidence_with_confidence()`**:
```python
# Before: return evidence, confidence

# After: return Evidence objects
return [Evidence(...) for sentence in candidates]
```

3. **Add auto JD processing**:
```python
# New endpoint
@app.post("/analyze/auto")
async def analyze_auto(jd_text: str, cv_file: UploadFile):
    job_profile = jd_extractor.extract_requirements(jd_text)
    # ... rest stays same
```

## Benefits of Universal Architecture

✅ **Scale**: Works for any industry (healthcare, aviation, finance, etc.)  
✅ **Maintenance**: No more hand-coding skill aliases  
✅ **Accuracy**: Better coverage through embeddings + ontologies  
✅ **Flexibility**: Auto-adapt to new roles and skills  
✅ **Localization**: Multilingual support out of the box  
✅ **Fairness**: Reduced bias through systematic approaches  

## Migration Strategy

**Option A: Gradual (Recommended)**
- Keep current system running
- Add ontology as optional feature flag
- A/B test new components
- Switch over skill by skill

**Option B: Big Bang**
- Rewrite core in 2-3 weeks
- Higher risk but faster to full benefits

Your current architecture is excellent foundation! The migration path is clear and achievable. 🚀
