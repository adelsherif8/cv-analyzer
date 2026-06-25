"""
Skill suggestion service for job profile creation
"""

from typing import List, Dict
import re

def suggest_skills_for_role(title: str, description: str) -> List[Dict[str, any]]:
    """
    Suggest relevant skills based on job title and description
    Returns list of {name, weight, category, is_bonus}
    """
    title_lower = title.lower()
    desc_lower = description.lower()
    combined_text = f"{title_lower} {desc_lower}"
    
    # Define skill categories and suggestions
    skill_database = {
        # Frontend Development
        'frontend': {
            'patterns': ['frontend', 'front-end', 'ui', 'user interface', 'web developer', 'react', 'angular', 'vue'],
            'core_skills': [
                {'name': 'HTML', 'weight': 0.2, 'category': 'Frontend'},
                {'name': 'CSS', 'weight': 0.2, 'category': 'Frontend'},
                {'name': 'JavaScript', 'weight': 0.3, 'category': 'Frontend'},
                {'name': 'React', 'weight': 0.15, 'category': 'Frontend'},
                {'name': 'Git', 'weight': 0.15, 'category': 'Tools'}
            ],
            'bonus_skills': [
                {'name': 'TypeScript', 'weight': 0.1, 'category': 'Frontend'},
                {'name': 'Sass/SCSS', 'weight': 0.05, 'category': 'Frontend'},
                {'name': 'Webpack', 'weight': 0.05, 'category': 'Tools'},
                {'name': 'Testing (Jest/Cypress)', 'weight': 0.05, 'category': 'Testing'}
            ]
        },
        
        # Shopify Development
        'shopify': {
            'patterns': ['shopify', 'e-commerce', 'ecommerce', 'liquid', 'theme'],
            'core_skills': [
                {'name': 'Liquid Templating', 'weight': 0.25, 'category': 'Shopify'},
                {'name': 'HTML', 'weight': 0.2, 'category': 'Frontend'},
                {'name': 'CSS', 'weight': 0.2, 'category': 'Frontend'},
                {'name': 'JavaScript', 'weight': 0.2, 'category': 'Frontend'},
                {'name': 'Shopify API', 'weight': 0.15, 'category': 'Shopify'}
            ],
            'bonus_skills': [
                {'name': 'Shopify Plus', 'weight': 0.1, 'category': 'Shopify'},
                {'name': 'GraphQL', 'weight': 0.08, 'category': 'API'},
                {'name': 'React', 'weight': 0.07, 'category': 'Frontend'},
                {'name': 'E-commerce Analytics', 'weight': 0.05, 'category': 'Analytics'}
            ]
        },
        
        # Data Science
        'data_science': {
            'patterns': ['data scientist', 'data science', 'machine learning', 'ml', 'analytics', 'data analyst'],
            'core_skills': [
                {'name': 'Python', 'weight': 0.3, 'category': 'Programming'},
                {'name': 'Machine Learning', 'weight': 0.25, 'category': 'Data Science'},
                {'name': 'SQL', 'weight': 0.2, 'category': 'Database'},
                {'name': 'Statistics', 'weight': 0.15, 'category': 'Mathematics'},
                {'name': 'Data Visualization', 'weight': 0.1, 'category': 'Analytics'}
            ],
            'bonus_skills': [
                {'name': 'TensorFlow/PyTorch', 'weight': 0.1, 'category': 'ML Frameworks'},
                {'name': 'R Programming', 'weight': 0.08, 'category': 'Programming'},
                {'name': 'Apache Spark', 'weight': 0.07, 'category': 'Big Data'},
                {'name': 'Docker', 'weight': 0.05, 'category': 'DevOps'}
            ]
        },
        
        # Backend Development
        'backend': {
            'patterns': ['backend', 'back-end', 'server', 'api', 'microservices', 'database'],
            'core_skills': [
                {'name': 'Python', 'weight': 0.25, 'category': 'Programming'},
                {'name': 'SQL', 'weight': 0.2, 'category': 'Database'},
                {'name': 'API Development', 'weight': 0.2, 'category': 'Backend'},
                {'name': 'Git', 'weight': 0.15, 'category': 'Tools'},
                {'name': 'Linux', 'weight': 0.1, 'category': 'Systems'},
                {'name': 'Database Design', 'weight': 0.1, 'category': 'Database'}
            ],
            'bonus_skills': [
                {'name': 'Docker', 'weight': 0.1, 'category': 'DevOps'},
                {'name': 'AWS', 'weight': 0.1, 'category': 'Cloud'},
                {'name': 'Redis', 'weight': 0.05, 'category': 'Database'},
                {'name': 'GraphQL', 'weight': 0.05, 'category': 'API'}
            ]
        },
        
        # DevOps
        'devops': {
            'patterns': ['devops', 'infrastructure', 'cloud', 'deployment', 'ci/cd', 'kubernetes'],
            'core_skills': [
                {'name': 'AWS', 'weight': 0.25, 'category': 'Cloud'},
                {'name': 'Docker', 'weight': 0.2, 'category': 'Containers'},
                {'name': 'Kubernetes', 'weight': 0.2, 'category': 'Orchestration'},
                {'name': 'Terraform', 'weight': 0.15, 'category': 'Infrastructure'},
                {'name': 'CI/CD', 'weight': 0.1, 'category': 'Automation'},
                {'name': 'Linux', 'weight': 0.1, 'category': 'Systems'}
            ],
            'bonus_skills': [
                {'name': 'Prometheus/Grafana', 'weight': 0.08, 'category': 'Monitoring'},
                {'name': 'Ansible', 'weight': 0.07, 'category': 'Configuration'},
                {'name': 'Python Scripting', 'weight': 0.05, 'category': 'Automation'}
            ]
        },
        
        # Digital Marketing
        'marketing': {
            'patterns': ['marketing', 'digital marketing', 'seo', 'social media', 'ppc', 'analytics'],
            'core_skills': [
                {'name': 'Google Analytics', 'weight': 0.25, 'category': 'Analytics'},
                {'name': 'SEO', 'weight': 0.2, 'category': 'Marketing'},
                {'name': 'Social Media Marketing', 'weight': 0.2, 'category': 'Marketing'},
                {'name': 'Content Marketing', 'weight': 0.15, 'category': 'Marketing'},
                {'name': 'PPC Advertising', 'weight': 0.1, 'category': 'Advertising'},
                {'name': 'Email Marketing', 'weight': 0.1, 'category': 'Marketing'}
            ],
            'bonus_skills': [
                {'name': 'Google Ads Certification', 'weight': 0.08, 'category': 'Certification'},
                {'name': 'Facebook Ads', 'weight': 0.07, 'category': 'Advertising'},
                {'name': 'Marketing Automation', 'weight': 0.05, 'category': 'Tools'}
            ]
        }
    }
    
    # Find matching skill categories
    matched_categories = []
    for category, data in skill_database.items():
        for pattern in data['patterns']:
            if pattern in combined_text:
                matched_categories.append(category)
                break
    
    # If no specific match, try to infer from common keywords
    if not matched_categories:
        if any(word in combined_text for word in ['developer', 'programming', 'software', 'engineer']):
            if any(word in combined_text for word in ['web', 'frontend', 'ui', 'react', 'angular']):
                matched_categories.append('frontend')
            elif any(word in combined_text for word in ['backend', 'server', 'api', 'database']):
                matched_categories.append('backend')
        elif any(word in combined_text for word in ['data', 'analytics', 'science', 'machine learning']):
            matched_categories.append('data_science')
        elif any(word in combined_text for word in ['marketing', 'seo', 'social']):
            matched_categories.append('marketing')
    
    # Combine suggestions from matched categories
    suggestions = {
        'core_skills': [],
        'bonus_skills': []
    }
    
    for category in matched_categories:
        if category in skill_database:
            suggestions['core_skills'].extend(skill_database[category]['core_skills'])
            suggestions['bonus_skills'].extend(skill_database[category]['bonus_skills'])
    
    # Remove duplicates while preserving order
    seen_core = set()
    seen_bonus = set()
    
    unique_core = []
    for skill in suggestions['core_skills']:
        if skill['name'] not in seen_core:
            seen_core.add(skill['name'])
            unique_core.append({**skill, 'is_bonus': False})
    
    unique_bonus = []
    for skill in suggestions['bonus_skills']:
        if skill['name'] not in seen_bonus and skill['name'] not in seen_core:
            seen_bonus.add(skill['name'])
            unique_bonus.append({**skill, 'is_bonus': True})
    
    return {
        'core_skills': unique_core[:6],  # Limit to 6 core skills
        'bonus_skills': unique_bonus[:4]  # Limit to 4 bonus skills
    }
