"""
Universal Skill Ontology - Phase 1 Implementation

Vector-based skill matching system that replaces hard-coded aliases
with semantic embeddings and fuzzy matching.
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import faiss
from rapidfuzz import fuzz, process
import logging

logger = logging.getLogger(__name__)

@dataclass
class SkillNode:
    """Single skill in the ontology"""
    skill_id: str
    canonical_label: str
    aliases: List[str]
    domains: List[str]  # ['frontend', 'healthcare', 'finance']
    typical_artifacts: List[str]  # ['jsx', '.py', 'GAAP']
    embedding: Optional[np.ndarray] = None

@dataclass
class SkillMatch:
    """Result of skill matching"""
    skill_id: str
    canonical_label: str
    similarity_score: float
    match_type: str  # 'semantic', 'fuzzy', 'exact'
    matched_alias: str

class UniversalSkillOntology:
    """
    Universal skill ontology using embeddings + fuzzy matching
    
    Replaces hard-coded SKILL_ALIAS_MAP with scalable vector search
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.embeddings_model = SentenceTransformer(model_name)
        self.skills: Dict[str, SkillNode] = {}
        self.vector_index: Optional[faiss.Index] = None
        self.alias_index: Dict[str, str] = {}  # alias -> skill_id
        self.skill_id_to_index: Dict[str, int] = {}
        self._initialized = False
        
    def load_from_data(self, skills_data: List[Dict[str, Any]]):
        """Load skills from structured data"""
        logger.info(f"Loading {len(skills_data)} skills into ontology...")
        
        # Parse skills
        embeddings_list = []
        for i, skill_data in enumerate(skills_data):
            skill_id = skill_data['skill_id']
            
            skill_node = SkillNode(
                skill_id=skill_id,
                canonical_label=skill_data['canonical_label'],
                aliases=skill_data.get('aliases', []),
                domains=skill_data.get('domains', []),
                typical_artifacts=skill_data.get('typical_artifacts', [])
            )
            
            # Generate embedding for canonical label
            embedding = self.embeddings_model.encode([skill_node.canonical_label])[0]
            skill_node.embedding = embedding
            embeddings_list.append(embedding)
            
            self.skills[skill_id] = skill_node
            self.skill_id_to_index[skill_id] = i
            
            # Build alias index for fuzzy matching
            for alias in skill_node.aliases:
                self.alias_index[alias.lower()] = skill_id
        
        # Build FAISS vector index
        embeddings_matrix = np.array(embeddings_list).astype('float32')
        dimension = embeddings_matrix.shape[1]
        
        # Use IndexFlatIP for cosine similarity
        self.vector_index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_matrix)
        self.vector_index.add(embeddings_matrix)
        
        self._initialized = True
        logger.info(f"Ontology initialized with {len(self.skills)} skills, {len(self.alias_index)} aliases")
    
    def nearest_skills(self, phrase: str, k: int = 8, 
                      cos_thresh: float = 0.78, fuzz_thresh: int = 86) -> List[SkillMatch]:
        """
        Find nearest skills using semantic + fuzzy matching
        
        This is the core replacement for get_aliases_for_skill()
        """
        if not self._initialized:
            logger.warning("Ontology not initialized")
            return []
        
        phrase_lower = phrase.lower().strip()
        matches = []
        
        # 1. Exact alias match (highest priority)
        if phrase_lower in self.alias_index:
            skill_id = self.alias_index[phrase_lower]
            skill = self.skills[skill_id]
            matches.append(SkillMatch(
                skill_id=skill_id,
                canonical_label=skill.canonical_label,
                similarity_score=1.0,
                match_type='exact',
                matched_alias=phrase_lower
            ))
        
        # 2. Semantic vector search
        try:
            query_embedding = self.embeddings_model.encode([phrase])[0:1].astype('float32')
            faiss.normalize_L2(query_embedding)
            
            similarities, indices = self.vector_index.search(query_embedding, min(k * 2, len(self.skills)))
            
            for sim, idx in zip(similarities[0], indices[0]):
                if sim >= cos_thresh:
                    skill_id = list(self.skill_id_to_index.keys())[
                        list(self.skill_id_to_index.values()).index(idx)
                    ]
                    skill = self.skills[skill_id]
                    
                    # Avoid duplicates from exact match
                    if not any(m.skill_id == skill_id for m in matches):
                        matches.append(SkillMatch(
                            skill_id=skill_id,
                            canonical_label=skill.canonical_label,
                            similarity_score=float(sim),
                            match_type='semantic',
                            matched_alias=skill.canonical_label
                        ))
        except Exception as e:
            logger.warning(f"Vector search failed for '{phrase}': {e}")
        
        # 3. Fuzzy matching fallback
        fuzzy_matches = process.extract(
            phrase_lower, 
            self.alias_index.keys(), 
            scorer=fuzz.token_set_ratio, 
            limit=k
        )
        
        for alias, score, _ in fuzzy_matches:
            if score >= fuzz_thresh:
                skill_id = self.alias_index[alias]
                skill = self.skills[skill_id]
                
                # Avoid duplicates
                if not any(m.skill_id == skill_id for m in matches):
                    matches.append(SkillMatch(
                        skill_id=skill_id,
                        canonical_label=skill.canonical_label,
                        similarity_score=score / 100.0,
                        match_type='fuzzy',
                        matched_alias=alias
                    ))
        
        # Sort by similarity and return top k
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:k]
    
    def get_aliases_for_skill_id(self, skill_id: str) -> List[str]:
        """Get all aliases for a specific skill ID"""
        if skill_id not in self.skills:
            return []
        return self.skills[skill_id].aliases
    
    def expand_skill_semantically(self, skill_name: str, threshold: float = 0.7) -> List[str]:
        """
        Expand a skill to related skills using semantic similarity
        
        This replaces expand_skill_to_subskills() with semantic understanding
        """
        matches = self.nearest_skills(skill_name, k=15, cos_thresh=threshold)
        
        # Get all aliases from matching skills
        expanded_aliases = []
        for match in matches:
            skill = self.skills[match.skill_id]
            expanded_aliases.extend(skill.aliases)
        
        # Remove duplicates and return
        return list(dict.fromkeys(expanded_aliases))

def create_sample_ontology() -> List[Dict[str, Any]]:
    """
    Create sample skill ontology data
    
    In production, this would be loaded from ESCO, O*NET, etc.
    """
    return [
        {
            "skill_id": "react_development",
            "canonical_label": "React.js Development",
            "aliases": [
                "react", "reactjs", "react.js", "jsx", "react hooks", "hooks",
                "component", "components", "state management", "useState", "useEffect",
                "redux", "context api", "react router", "react native"
            ],
            "domains": ["frontend", "web_development", "javascript"],
            "typical_artifacts": ["jsx", ".tsx", "package.json", "react-scripts"]
        },
        {
            "skill_id": "shopify_development", 
            "canonical_label": "Shopify Development",
            "aliases": [
                "shopify", "liquid", "liquid templating", ".liquid", "theme", "themes",
                "shopify theme", "theme customization", "sections schema", "snippets",
                "metafields", "shopify editor", "dawn", "checkout", "shopify api",
                "app embed", "cart.js", "storefront api", "shopify plus"
            ],
            "domains": ["ecommerce", "web_development", "retail"],
            "typical_artifacts": [".liquid", "theme.json", "cart.js", "shopify-cli"]
        },
        {
            "skill_id": "javascript_development",
            "canonical_label": "JavaScript Development", 
            "aliases": [
                "javascript", "js", "es6", "es2015", "es2020", "typescript", "ts",
                "async/await", "fetch", "axios", "webpack", "vite", "babel", 
                "eslint", "prettier", "jest", "node.js", "nodejs", "npm", "yarn"
            ],
            "domains": ["frontend", "backend", "web_development"],
            "typical_artifacts": [".js", ".ts", "package.json", "webpack.config.js"]
        },
        {
            "skill_id": "html_css_responsive",
            "canonical_label": "HTML/CSS & Responsive Design",
            "aliases": [
                "html", "html5", "css", "css3", "responsive design", "mobile-first",
                "tailwind", "tailwindcss", "bootstrap", "sass", "scss", "less",
                "flexbox", "css grid", "grid", "media queries", "responsive"
            ],
            "domains": ["frontend", "web_development", "ui_design"],
            "typical_artifacts": [".html", ".css", ".scss", "tailwind.config.js"]
        },
        {
            "skill_id": "api_integration",
            "canonical_label": "API Integration & Performance",
            "aliases": [
                "api", "rest api", "restful", "graphql", "webhooks", "integration",
                "microservices", "razorpay", "stripe", "payment integration", 
                "crm integration", "zapier", "gohighlevel", "lighthouse", 
                "core web vitals", "performance optimization", "caching", "cdn"
            ],
            "domains": ["backend", "integration", "performance"],
            "typical_artifacts": ["api.js", "webhooks", "openapi.json"]
        },
        {
            "skill_id": "python_development",
            "canonical_label": "Python Development",
            "aliases": [
                "python", "python3", "django", "flask", "fastapi", "pandas", 
                "numpy", "scikit-learn", "pip", "virtualenv", "conda", "jupyter",
                "matplotlib", "seaborn", "pytest", "black", "flake8"
            ],
            "domains": ["backend", "data_science", "automation"],
            "typical_artifacts": [".py", "requirements.txt", "pyproject.toml", "Pipfile"]
        },
        {
            "skill_id": "machine_learning",
            "canonical_label": "Machine Learning & AI",
            "aliases": [
                "machine learning", "ml", "artificial intelligence", "ai",
                "tensorflow", "pytorch", "keras", "deep learning", "neural networks",
                "nlp", "natural language processing", "computer vision", "cv",
                "data science", "model training", "supervised learning", "unsupervised learning"
            ],
            "domains": ["data_science", "ai", "research"],
            "typical_artifacts": [".ipynb", "model.pkl", "requirements.txt"]
        },
        {
            "skill_id": "aws_cloud",
            "canonical_label": "Amazon Web Services (AWS)",
            "aliases": [
                "aws", "amazon web services", "ec2", "s3", "lambda", "rds",
                "cloudformation", "eks", "ecs", "cloudwatch", "vpc", "iam",
                "api gateway", "dynamodb", "cognito", "sqs", "sns", "cloudfront"
            ],
            "domains": ["cloud", "devops", "infrastructure"],
            "typical_artifacts": ["cloudformation.yaml", "terraform", "aws-cli"]
        },
        {
            "skill_id": "docker_containers",
            "canonical_label": "Docker & Containerization", 
            "aliases": [
                "docker", "containers", "containerization", "kubernetes", "k8s",
                "docker-compose", "dockerfile", "pods", "deployments", "helm",
                "container orchestration", "microservices", "service mesh"
            ],
            "domains": ["devops", "infrastructure", "deployment"],
            "typical_artifacts": ["Dockerfile", "docker-compose.yml", "k8s.yaml"]
        },
        {
            "skill_id": "leadership_management",
            "canonical_label": "Leadership & Team Management",
            "aliases": [
                "leadership", "team leadership", "team lead", "managed", "mentored",
                "supervised", "led team", "project management", "stakeholder management",
                "team management", "people management", "agile", "scrum", "kanban"
            ],
            "domains": ["management", "soft_skills", "project_management"],
            "typical_artifacts": ["jira", "confluence", "slack"]
        },
        # Healthcare example
        {
            "skill_id": "clinical_nursing",
            "canonical_label": "Clinical Nursing",
            "aliases": [
                "nursing", "clinical nursing", "patient care", "medication administration",
                "iv therapy", "wound care", "vital signs", "charting", "ehr",
                "epic", "cerner", "meditech", "ccrn", "acls", "bls", "pals"
            ],
            "domains": ["healthcare", "nursing", "patient_care"],
            "typical_artifacts": ["epic", "cerner", "medication_cart"]
        },
        # Finance example  
        {
            "skill_id": "financial_analysis",
            "canonical_label": "Financial Analysis & Reporting",
            "aliases": [
                "financial analysis", "financial modeling", "valuation", "dcf",
                "financial reporting", "gaap", "ifrs", "sox", "excel", "bloomberg",
                "capital markets", "investment analysis", "risk analysis", "cfa"
            ],
            "domains": ["finance", "accounting", "investment"],
            "typical_artifacts": ["excel", "bloomberg_terminal", "quickbooks"]
        }
    ]

# Global ontology instance (will be initialized on startup)
global_ontology = UniversalSkillOntology()

def initialize_ontology():
    """Initialize the global ontology"""
    try:
        sample_data = create_sample_ontology()
        global_ontology.load_from_data(sample_data)
        logger.info("Universal Skill Ontology initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ontology: {e}")
        return False
