"""
Focused LLM calls for each section type.
Each section gets a specialized prompt for better accuracy.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_student_info(section_text):
    """
    Extract student information from marksheet.
    Enhanced for Indian marksheets with better parent name extraction.
    """
    if not section_text or len(section_text.strip()) < 10:
        print("   ⚠️ No student info section text available")
        return {}
    
    # Truncate if too long
    if len(section_text) > 4000:
        section_text = section_text[:4000]
    
    prompt = f"""
You are extracting student information from an Indian marksheet.

Here is the STUDENT INFO SECTION from the marksheet:
---
{section_text}
---

Extract ONLY these fields and return valid JSON:
{{
    "student_name": "",
    "father_name": "",
    "mother_name": "",
    "roll_number": "",
    "registration_number": "",
    "date_of_birth": ""
}}

IMPORTANT: Look for these EXACT patterns in Indian marksheets:

For STUDENT NAME:
- "Name of the Candidate", "Candidate's Name", "Student Name", "Name:", "APPLICANT'S NAME"
- Usually appears near the top of the marksheet

For FATHER'S NAME:
- "Father's Name", "Father Name", "Name of Father", "FATHER'S NAME", "S/o:", "Son of"
- Often appears right after student name
- Sometimes written as "Shri [Name]" or "Mr. [Name]"

For MOTHER'S NAME:
- "Mother's Name", "Mother Name", "Name of Mother", "MOTHER'S NAME", "D/o:", "Daughter of"
- Often appears after father's name
- Sometimes written as "Smt [Name]" or "Mrs. [Name]"

For ROLL NUMBER:
- "Roll No.", "Roll Number", "Index No.", "Index Number", "Reg. No."
- Usually a numeric or alphanumeric code

For REGISTRATION NUMBER:
- "Registration No.", "Reg No.", "Unique ID", "Candidate ID"
- Often a longer number

For DATE OF BIRTH:
- "Date of Birth", "DOB", "Birth Date"
- Format: DD-MM-YYYY or DD/MM/YYYY

RULES:
- Remove prefixes like "Shri", "Smt", "Mr.", "Mrs.", "Dr." when extracting names
- Remove labels completely (extract only the value)
- If a field is not found in the text, use null
- Pay special attention to parent names - they are critical
- Return ONLY valid JSON, no extra text

Example output for a typical Indian marksheet:
{{
    "student_name": "AHANA TALUKDAR",
    "father_name": "ARUNANSU TALUKDAR",
    "mother_name": "PAYEL TALUKDAR",
    "roll_number": "2237346/093",
    "registration_number": "7278509",
    "date_of_birth": "15-08-2005"
}}
"""
    
    result_str = _call_llm(prompt, "student_info_extractor")
    
    try:
        result = json.loads(result_str)
        
        # Clean up any prefixes that might have been missed
        for field in ['father_name', 'mother_name']:
            if result.get(field):
                # Remove common prefixes
                cleaned = re.sub(r'^(Shri|Smt|Mr\.|Mrs\.|Dr\.|M/s)\s+', '', result[field], flags=re.IGNORECASE)
                result[field] = cleaned.strip()
        
        return result
    except json.JSONDecodeError:
        print(f"   ⚠️ Failed to parse student info JSON")
        return {}

def extract_subjects(section_text):
    """
    Extract subjects and marks from the table section.
    Specialized for the marks table only.
    """
    if not section_text or len(section_text.strip()) < 20:
        print("   ⚠️ No subject table section text available")
        return {"subjects": []}
    
    if len(section_text) > 6000:
        section_text = section_text[:6000]
    
    prompt = f"""
You are extracting subject marks from an Indian marksheet.

Here is the SUBJECT MARKS TABLE SECTION from the marksheet:
---
{section_text}
---

Extract ALL subjects with their marks and return valid JSON:
{{
    "subjects": [
        {{"subject": "", "marks": null, "max_marks": null, "grade": null, "code": null}}
    ]
}}

RULES:
- Look for subject names followed by numbers (marks)
- Common patterns: "MATHEMATICS 85", "ENGLISH 78/100", "PHYSICS - 75", "CHEMISTRY A1"
- Subject name is usually text, marks are numbers
- If max marks is present (like "85/100"), extract both marks (85) and max_marks (100)
- Extract grade if present (A, B+, A1, etc.)
- Include EVERY subject you find
- Return ONLY valid JSON

Example output:
{{
    "subjects": [
        {{"subject": "MATHEMATICS", "marks": 85, "max_marks": 100, "grade": "A", "code": "041"}},
        {{"subject": "ENGLISH", "marks": 78, "max_marks": 100, "grade": "B+", "code": "301"}},
        {{"subject": "PHYSICS", "marks": 75, "max_marks": null, "grade": "B", "code": "042"}},
        {{"subject": "CHEMISTRY", "marks": 82, "max_marks": 100, "grade": "A-", "code": null}}
    ]
}}
"""
    
    result_str = _call_llm(prompt, "subject_extractor")
    try:
        data = json.loads(result_str)
        # Ensure we have a subjects list
        if isinstance(data, dict) and 'subjects' in data:
            return data
        elif isinstance(data, list):
            # Sometimes LLM returns just the list
            return {"subjects": data}
        else:
            return {"subjects": []}
    except json.JSONDecodeError:
        print(f"   ⚠️ Failed to parse subjects JSON")
        return {"subjects": []}


def extract_totals(section_text):
    """
    Extract totals and summary information.
    Specialized for the bottom/totals section only.
    """
    if not section_text or len(section_text.strip()) < 10:
        print("   ⚠️ No totals section text available")
        return {}
    
    if len(section_text) > 3000:
        section_text = section_text[:3000]
    
    prompt = f"""
You are extracting total marks and summary from an Indian marksheet.

Here is the TOTALS/RESULT SECTION from the marksheet:
---
{section_text}
---

Extract these fields and return valid JSON:
{{
    "total_marks": null,
    "maximum_marks": null,
    "percentage": null,
    "result": "",
    "division": "",
    "cgpa": null,
    "grade": null
}}

RULES:
- total_marks: The marks obtained (e.g., 425, 85.5)
- maximum_marks: The total possible marks (e.g., 500)
- percentage: The percentage score (e.g., 85.0)
- result: "PASS" or "FAIL" (use uppercase)
- division: "FIRST DIVISION", "SECOND DIVISION", "DISTINCTION", etc.
- cgpa: If CGPA is mentioned (e.g., 8.5)
- grade: Overall grade if mentioned (e.g., "A", "A+")
- All numbers should be floats or null
- Return ONLY valid JSON

Example output:
{{
    "total_marks": 425,
    "maximum_marks": 500,
    "percentage": 85.0,
    "result": "PASS",
    "division": "FIRST DIVISION",
    "cgpa": null,
    "grade": "A"
}}
"""
    
    result_str = _call_llm(prompt, "totals_extractor")
    try:
        result = json.loads(result_str)
        return result
    except json.JSONDecodeError:
        print(f"   ⚠️ Failed to parse totals JSON")
        return {}


def _call_llm(prompt, system_role):
    """Helper function to call Groq API"""
    try:
        print(f"   🤖 Calling LLM for {system_role}...")
        
        # Make the API call
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a precise {system_role}. Output ONLY valid JSON. Never add explanations or markdown formatting."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,  # Zero temperature for consistent results
            max_tokens=2000
        )
        
        # Get response
        response = chat_completion.choices[0].message.content
        
        if not response:
            print(f"   ⚠️ Empty response from LLM for {system_role}")
            return "{}"
        
        # Clean up the response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        response = response.strip()
        
        # Attempt to extract JSON if there's extra text
        # Look for JSON object pattern
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group()
        
        # Validate JSON (this will raise exception if invalid)
        json.loads(response)
        
        print(f"   ✅ LLM response received and validated ({len(response)} chars)")
        return response
        
    except json.JSONDecodeError as e:
        print(f"   ⚠️ JSON decode error for {system_role}: {e}")
        print(f"   Response preview: {response[:200] if 'response' in locals() else 'None'}")
        return "{}"
        
    except Exception as e:
        print(f"   ❌ LLM call failed for {system_role}: {e}")
        return "{}"


# Optional: Add a helper function for regex-based subject extraction as fallback
def extract_subjects_regex(section_text):
    """
    Fallback method: Extract subjects using regex patterns.
    This can be used if LLM fails or for quick extraction.
    """
    subjects = []
    
    # Pattern 1: Subject name followed by marks (e.g., "MATHEMATICS 85")
    pattern1 = r'([A-Z][A-Z\s]+?)\s+(\d+(?:\.\d+)?)(?:/\s*(\d+(?:\.\d+)?))?'
    
    # Pattern 2: Subject with hyphen (e.g., "PHYSICS - 85")
    pattern2 = r'([A-Z][A-Z\s]+?)\s*-\s*(\d+(?:\.\d+)?)'
    
    # Pattern 3: Code + Subject + Marks (e.g., "041 MATHEMATICS 85")
    pattern3 = r'(\d+)\s+([A-Z][A-Z\s]+?)\s+(\d+(?:\.\d+)?)'
    
    lines = section_text.split('\n')
    for line in lines:
        # Try pattern3 first (has code)
        match = re.search(pattern3, line)
        if match:
            subjects.append({
                "subject": match.group(2).strip(),
                "marks": float(match.group(3)) if match.group(3) else None,
                "max_marks": None,
                "grade": None,
                "code": match.group(1)
            })
            continue
        
        # Try pattern1
        match = re.search(pattern1, line)
        if match:
            subjects.append({
                "subject": match.group(1).strip(),
                "marks": float(match.group(2)) if match.group(2) else None,
                "max_marks": float(match.group(3)) if match.group(3) else None,
                "grade": None,
                "code": None
            })
            continue
        
        # Try pattern2
        match = re.search(pattern2, line)
        if match:
            subjects.append({
                "subject": match.group(1).strip(),
                "marks": float(match.group(2)) if match.group(2) else None,
                "max_marks": None,
                "grade": None,
                "code": None
            })
    
    return subjects