"""
Main parser that orchestrates layout detection + focused LLM extraction.
"""

import json
import sys
from .layout_parser import LayoutParser  # ← This is your EasyOCR version
from .llm_extractor import extract_student_info, extract_subjects, extract_totals


def parse_sectioned(file_path, debug=True):
    """
    Complete pipeline: Layout Detection → Focused LLM → Structured JSON
    
    This uses PaddleOCR's layout analysis to first identify sections,
    then sends each section to a specialized LLM prompt.
    """
    
    print("\n" + "="*70)
    print("🎯 SECTION-BASED PARSER WITH LAYOUT DETECTION (PaddleOCR)")
    print("="*70)
    
    # ========== STEP 1: Layout Detection ==========
    print("\n📌 STEP 1: Detecting document sections with PaddleOCR layout analysis...")
    
    layout_parser = LayoutParser(debug=debug)
    sections = layout_parser.extract_sections(file_path)
    
    if not sections:
        print("❌ Failed to extract sections from document")
        return {"error": "Failed to extract sections", "fallback_used": False}
    
    # Print what sections were found
    print("\n✅ Sections detected:")
    for section_name in sections.keys():
        if sections[section_name] and section_name != 'full_text':
            print(f"   - {section_name}: {len(sections[section_name])} chars")
    
    # ========== STEP 2: Focused LLM Extraction ==========
    print("\n📌 STEP 2: Extracting data with specialized LLM calls...")
    
    result = {}
    
    # Extract student info
    if sections.get('student_info'):
        print("\n👤 Extracting Student Information...")
        student_data = extract_student_info(sections['student_info'])
        result.update(student_data)
        print(f"   → Student: {result.get('student_name', 'Not found')}")
        print(f"   → Roll No: {result.get('roll_number', 'Not found')}")
    
    # Extract subjects
    if sections.get('subject_table'):
        print("\n📚 Extracting Subject Marks...")
        subjects_data = extract_subjects(sections['subject_table'])
        result['subjects'] = subjects_data.get('subjects', [])
        print(f"   → Found {len(result['subjects'])} subjects")
        for subj in result['subjects'][:3]:
            print(f"      - {subj.get('subject', '?')}: {subj.get('marks', '?')} marks")
        if len(result['subjects']) > 3:
            print(f"      ... and {len(result['subjects']) - 3} more")
    
    # Extract totals
    totals_text = ""
    if sections.get('totals'):
        totals_text += sections['totals']
    if sections.get('result'):
        totals_text += "\n" + sections['result']
    
    if totals_text:
        print("\n💰 Extracting Totals & Result...")
        totals_data = extract_totals(totals_text)
        result.update(totals_data)
        print(f"   → Total Marks: {result.get('total_marks', 'Not found')}")
        print(f"   → Percentage: {result.get('percentage', 'Not found')}")
        print(f"   → Result: {result.get('result', 'Not found')}")
    
    # ========== STEP 3: Handle Fallback ==========
    has_data = any([
        result.get('student_name'),
        result.get('subjects'),
        result.get('total_marks') is not None
    ])
    
    if not has_data and sections.get('full_text'):
        print("\n⚠️ No data extracted from individual sections - trying full document...")
        result = _full_document_fallback(sections['full_text'], result)
        result['fallback_used'] = True
    else:
        result['fallback_used'] = False
    
    # ========== STEP 4: Add Metadata ==========
    result['_metadata'] = {
        'parser_type': 'sectioned_paddleocr',
        'sections_found': {k: len(v) for k, v in sections.items() if v and k != 'full_text'},
        'sections_used': {
            'student': bool(sections.get('student_info')),
            'subjects': bool(sections.get('subject_table')),
            'totals': bool(sections.get('totals') or sections.get('result'))
        }
    }
    
    # ========== SUMMARY ==========
    print("\n" + "="*70)
    print("📊 EXTRACTION SUMMARY")
    print("="*70)
    print(f"   Student Name: {result.get('student_name', '❌ Not found')}")
    print(f"   Roll Number: {result.get('roll_number', '❌ Not found')}")
    print(f"   Subjects: {len(result.get('subjects', []))} found")
    print(f"   Total Marks: {result.get('total_marks', '❌ Not found')}")
    print(f"   Percentage: {result.get('percentage', '❌ Not found')}")
    print(f"   Result: {result.get('result', '❌ Not found')}")
    print("="*70 + "\n")
    
    return result
def _full_document_fallback(full_text, current_result):
    """Fallback: Send entire document to LLM if section extraction failed"""
    try:
        from groq import Groq
        import os
        import json
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        if len(full_text) > 6000:
            full_text = full_text[:6000]
        
        prompt = f"""
Extract ALL information from this Indian marksheet. Return ONLY valid JSON.

Text:
{full_text}

Required JSON:
{{
    "student_name": "",
    "father_name": "",
    "mother_name": "",
    "roll_number": "",
    "subjects": [{{"subject": "", "marks": null, "max_marks": null, "grade": null}}],
    "total_marks": null,
    "maximum_marks": null,
    "percentage": null,
    "result": "",
    "division": ""
}}

Return ONLY valid JSON, no other text.
"""
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You extract structured data from Indian marksheets. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=3000
        )
        
        fallback_data = json.loads(response.choices[0].message.content)
        
        # Update current_result with fallback data
        for key in ['student_name', 'father_name', 'mother_name', 'roll_number', 
                    'total_marks', 'maximum_marks', 'percentage', 'result', 'division']:
            if fallback_data.get(key):
                current_result[key] = fallback_data[key]
        
        if fallback_data.get('subjects'):
            current_result['subjects'] = fallback_data['subjects']
        
        if '_metadata' not in current_result:
            current_result['_metadata'] = {}
        current_result['_metadata']['fallback_success'] = True
        print("   ✅ Fallback extraction successful!")
        
    except Exception as e:
        print(f"   ❌ Fallback failed: {e}")
        if '_metadata' not in current_result:
            current_result['_metadata'] = {}
        current_result['_metadata']['fallback_error'] = str(e)
    
    return current_result