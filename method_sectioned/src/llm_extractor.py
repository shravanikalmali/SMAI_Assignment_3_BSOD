"""
Focused LLM calls for each section type.
Each section gets a specialized prompt for better accuracy.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_student_info(section_text):
    """
    Extract student information from marksheet.
    Specialized for the student info section only.
    """
    if not section_text or len(section_text.strip()) < 10:
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

RULES:
- Look for patterns like "Name:", "Student Name:", "Roll No:", "Reg No:", "Father:", "Mother:", "DOB:"
- Remove the labels from the values (extract just "RAHUL KUMAR", not "Name: RAHUL KUMAR")
- If a field is not found, use null
- Return ONLY valid JSON, no extra text

Example output:
{{
    "student_name": "RAHUL KUMAR",
    "father_name": "RAMESH KUMAR",
    "mother_name": "SUNITA KUMAR",
    "roll_number": "12345",
    "registration_number": "REG2024001",
    "date_of_birth": "15-08-2005"
}}
"""
    
    return _call_llm(prompt, "student_info_extractor")


def extract_subjects(section_text):
    """
    Extract subjects and marks from the table section.
    Specialized for the marks table only.
    """
    if not section_text or len(section_text.strip()) < 20:
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
    
    result = _call_llm(prompt, "subject_extractor")
    try:
        data = json.loads(result)
        return data if 'subjects' in data else {"subjects": []}
    except:
        return {"subjects": []}


def extract_totals(section_text):
    """
    Extract totals and summary information.
    Specialized for the bottom/totals section only.
    """
    if not section_text or len(section_text.strip()) < 10:
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
- result: "PASS" or "FAIL"
- division: "FIRST DIVISION", "SECOND DIVISION", "DISTINCTION", etc.
- cgpa: If CGPA is mentioned (e.g., 8.5)
- grade: Overall grade if mentioned (e.g., "A", "A+")
- All numbers should be floats
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
    
    return _call_llm(prompt, "totals_extractor")


def _call_llm(prompt, system_role):
    """Helper function to call Groq API"""
    try:
        print(f"   🤖 Calling LLM for {system_role}...")
        
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
        
        response = chat_completion.choices[0].message.content
        response = response.strip()
        
        # Clean up any markdown formatting
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # Validate JSON
        json.loads(response)
        
        print(f"   ✅ LLM response received ({len(response)} chars)")
        return response
        
    except json.JSONDecodeError as e:
        print(f"   ⚠️ JSON decode error: {e}")
        print(f"   Raw response: {response[:200] if 'response' in locals() else 'None'}")
        return json.dumps({"error": f"JSON parse failed: {str(e)}"})
        
    except Exception as e:
        print(f"   ❌ LLM call failed: {e}")
        return json.dumps({"error": str(e)})