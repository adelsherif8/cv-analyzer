#!/usr/bin/env python3
"""Debug script to test AI response parsing"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sample prompt and CV text
prompt = """You are an HR technical screener for front-end and e-commerce roles. 
Given a Job Profile (title, description, required skills with weights) and a CV text, 
you MUST (1) infer a 0-1 match score for each required skill with short bullet evidence, 
(2) list red flags if present (e.g., no portfolio links, exaggerated claims, no Shopify proof), 
(3) return a compact, strictly valid JSON with this shape:

{
  "skill_matches": [
    {"name": "Liquid", "match": 0.82, "evidence": ["custom sections", "snippets", "theme app extensions"]},
    {"name": "Shopify development", "match": 0.75, "evidence": ["3 themes shipped", "Dawn customization"]}
  ],
  "experience_years": 3.5,
  "project_evidence": ["store speed audit", "A/B tests on PDP"],
  "red_flags": ["no GitHub links"]
}

Do NOT include commentary outside the JSON. Use conservative estimates. If uncertain, lower the match.

Job Profile:
Title: Front-End Developer
Description: Build modern web applications using React and TypeScript
Required Skills:
- React (weight: 0.4)
- TypeScript (weight: 0.3)
- JavaScript (weight: 0.2)
- HTML/CSS (weight: 0.1)

CV Text:
Experienced software developer with 5 years in web development. Expert in React, TypeScript, and modern JavaScript. Built multiple e-commerce platforms and SPAs. Strong HTML/CSS skills with responsive design expertise.
"""

try:
    print("Testing AI response...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    
    result_text = response.choices[0].message.content
    print(f"Raw AI Response:\n{result_text}")
    print("-" * 50)
    
    # Try parsing
    try:
        parsed = json.loads(result_text)
        print("JSON parsing successful!")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print(f"Problematic content: {result_text[:200]}...")
        
        # Try extraction logic
        result_text = result_text.strip()
        if result_text.startswith("```json"):
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if start != -1 and end != 0:
                extracted = result_text[start:end]
                print(f"Extracted JSON: {extracted}")
                try:
                    parsed = json.loads(extracted)
                    print("Extraction successful!")
                    print(json.dumps(parsed, indent=2))
                except json.JSONDecodeError as e2:
                    print(f"Extraction also failed: {e2}")

except Exception as e:
    print(f"API call failed: {e}")
