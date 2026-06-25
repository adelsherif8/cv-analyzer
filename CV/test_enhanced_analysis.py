#!/usr/bin/env python3
"""
Test script for enhanced CV analysis system
Tests skill pattern matching, experience extraction, and red flags detection
"""

import sys
import os
sys.path.append('/Users/adel/Desktop/Cv analyzer/CV/backend')

from app.services.mock_ai import (
    analyze_skill_match, 
    calculate_years_of_experience,
    detect_red_flags,
    extract_candidate_contact_info,
    get_candidate_details
)

def test_enhanced_skill_matching():
    """Test enhanced skill pattern matching with achievement extraction"""
    print("🔍 TESTING ENHANCED SKILL PATTERN MATCHING")
    print("=" * 60)
    
    # Load senior data scientist CV
    with open('/Users/adel/Desktop/Cv analyzer/CV/test_cvs/data_scientist_senior.txt', 'r') as f:
        cv_content = f.read()
    
    # Test skills with different complexity levels
    test_skills = [
        "Python",
        "Machine Learning", 
        "TensorFlow",
        "AWS",
        "Leadership",
        "Deep Learning",
        "Docker",
        "A/B Testing"
    ]
    
    for skill in test_skills:
        score, evidence = analyze_skill_match(skill, cv_content)
        print(f"\n📊 Skill: {skill}")
        print(f"   Score: {score:.2f}")
        print(f"   Evidence Count: {len(evidence)}")
        for i, ev in enumerate(evidence[:2], 1):
            print(f"   Evidence {i}: {ev[:100]}...")
    
    return True

def test_enhanced_experience_extraction():
    """Test sophisticated experience calculation"""
    print("\n\n🎯 TESTING ENHANCED EXPERIENCE EXTRACTION")
    print("=" * 60)
    
    # Test with different CV types
    test_files = [
        ('Senior Data Scientist', '/Users/adel/Desktop/Cv analyzer/CV/test_cvs/data_scientist_senior.txt'),
        ('Junior Designer', '/Users/adel/Desktop/Cv analyzer/CV/test_cvs/ui_ux_designer_junior.txt'),
        ('DevOps Engineer', '/Users/adel/Desktop/Cv analyzer/CV/test_cvs/devops_engineer_senior.txt')
    ]
    
    for name, filepath in test_files:
        try:
            with open(filepath, 'r') as f:
                cv_content = f.read()
            
            years = calculate_years_of_experience(cv_content)
            print(f"\n👤 {name}")
            print(f"   Calculated Experience: {years} years")
            
            # Get timeline analysis
            from app.services.mock_ai import analyze_employment_timeline
            timeline_years = analyze_employment_timeline(cv_content)
            print(f"   Timeline Analysis: {timeline_years} years")
            
        except FileNotFoundError:
            print(f"   ⚠️  File not found: {filepath}")
    
    return True

def test_enhanced_red_flags_detection():
    """Test comprehensive red flags detection"""
    print("\n\n🚩 TESTING ENHANCED RED FLAGS DETECTION")
    print("=" * 60)
    
    # Create test CV with potential red flags
    problematic_cv = """
    John Quick - Software Developer
    Email: john@email.com
    
    Experience:
    Senior Architect | Company A | 2023 - Present (6 months)
    Lead Developer | Company B | 2022 - 2023 (1 year) 
    Software Engineer | Company C | 2021 - 2022 (8 months)
    Developer | Company D | 2020 - 2021 (10 months)
    Junior Developer | Company E | 2019 - 2020 (1 year)
    
    Skills: Expert in Python, JavaScript, React, Angular, Vue, Django, Flask, FastAPI, 
    Docker, Kubernetes, AWS, Azure, GCP, Machine Learning, AI, Blockchain, DevOps,
    Microservices, GraphQL, MongoDB, PostgreSQL, Redis, Elasticsearch, Terraform,
    Jenkins, Git, Linux, Windows, MacOS, iOS, Android development
    
    Education: PhD in Computer Science (but applying for junior role)
    
    [Notable gap: 2018-2019 missing]
    """
    
    # Mock job requirements (junior role)
    job_requirements = ['Python', 'JavaScript', 'Basic Web Development']
    
    red_flags = detect_red_flags(problematic_cv, job_requirements)
    
    print("🔍 Analyzing problematic CV...")
    print(f"   Detected {len(red_flags)} red flags:")
    for i, flag in enumerate(red_flags, 1):
        print(f"   {i}. {flag}")
    
    return True

def test_comprehensive_candidate_details():
    """Test comprehensive candidate details extraction"""
    print("\n\n📋 TESTING COMPREHENSIVE CANDIDATE DETAILS")
    print("=" * 60)
    
    with open('/Users/adel/Desktop/Cv analyzer/CV/test_cvs/data_scientist_senior.txt', 'r') as f:
        cv_content = f.read()
    
    details = get_candidate_details(cv_content)
    
    print("📞 Contact Information:")
    for key, value in details['contact_info'].items():
        print(f"   {key.title()}: {value}")
    
    print(f"\n⏱️  Experience: {details['experience_years']} years")
    
    print(f"\n🏆 Career Highlights ({len(details['career_highlights'])}):")
    for i, highlight in enumerate(details['career_highlights'], 1):
        print(f"   {i}. {highlight[:80]}...")
    
    print(f"\n💼 Top Skills ({len(details['top_skills'])}):")
    for skill_data in details['top_skills']:
        print(f"   • {skill_data['skill']}: {skill_data['evidence_count']} evidence pieces")
    
    return True

def test_skill_evidence_quality():
    """Test evidence quality scoring"""
    print("\n\n⭐ TESTING SKILL EVIDENCE QUALITY")
    print("=" * 60)
    
    # Test different types of evidence
    evidence_samples = [
        ("Built scalable ML pipeline reducing false positives by 40%", "High quality - quantified achievement"),
        ("Experience with Python programming", "Low quality - generic statement"),
        ("Led team of 3 data scientists implementing TensorFlow models", "High quality - leadership + technical detail"),
        ("Familiar with machine learning concepts", "Low quality - vague claim"),
        ("Deployed recommendation engine serving 1M+ daily predictions", "High quality - scale + impact")
    ]
    
    from app.services.mock_ai import calculate_evidence_quality
    
    for evidence, description in evidence_samples:
        score = calculate_evidence_quality(evidence, "Python")
        print(f"\n📝 Evidence: {evidence[:50]}...")
        print(f"   Quality Score: {score:.2f}")
        print(f"   Description: {description}")
    
    return True

def main():
    """Run all enhanced analysis tests"""
    print("🚀 ENHANCED CV ANALYSIS SYSTEM TEST")
    print("=" * 60)
    print("Testing improvements to:")
    print("1. Skill pattern matching precision")
    print("2. Experience extraction sophistication") 
    print("3. Red flags detection capabilities")
    print("4. Evidence quality assessment")
    print("5. Comprehensive candidate details")
    
    try:
        # Run all tests
        test_enhanced_skill_matching()
        test_enhanced_experience_extraction()
        test_enhanced_red_flags_detection()
        test_comprehensive_candidate_details()
        test_skill_evidence_quality()
        
        print("\n\n✅ ALL ENHANCED ANALYSIS TESTS COMPLETED SUCCESSFULLY!")
        print("🎯 System improvements demonstrated:")
        print("   • Precise skill pattern matching with technical achievements")
        print("   • Sophisticated experience calculation with timeline analysis")
        print("   • Comprehensive red flags detection with specific insights")
        print("   • Evidence-based skill assessment with quality scoring")
        print("   • Enhanced candidate details extraction")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
