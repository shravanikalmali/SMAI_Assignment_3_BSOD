"""
Main parser using trained section detection
"""

import json
import os
import sys

# Import local modules
# rm -f src/parser.py
from .layout_parser_trained import LayoutParserTrained
from .llm_extractor import extract_student_info, extract_subjects, extract_totals

def parse_sectioned_trained(file_path, debug=True):
    """Parse marksheet using trained section detector"""
    
    print("\n" + "="*70)
    print("🎯 TRAINED SECTION-BASED PARSER")
    print("="*70)
    
    # Step 1: Extract sections using trained model
    print("\n📌 STEP 1: Detecting sections with trained model...")
    layout_parser = LayoutParserTrained(debug=debug)
    sections = layout_parser.extract_sections(file_path)
    
    if not sections:
        return {"error": "Failed to extract sections"}
    
    # Step 2: Extract data from each section
    print("\n📌 STEP 2: Extracting data with LLM...")
    result = {}
    
    if sections.get('student_info'):
        print("\n👤 Extracting student info...")
        student_data = extract_student_info(sections['student_info'])
        result.update(student_data)
        if result.get('student_name'):
            print(f"   ✅ Student: {result['student_name']}")
    
    if sections.get('subject_table'):
        print("\n📚 Extracting subjects...")
        subjects_data = extract_subjects(sections['subject_table'])
        result['subjects'] = subjects_data.get('subjects', [])
        print(f"   ✅ Found {len(result['subjects'])} subjects")
    
    totals_text = sections.get('totals', '') + '\n' + sections.get('result', '')
    if totals_text.strip():
        print("\n💰 Extracting totals...")
        totals_data = extract_totals(totals_text)
        result.update(totals_data)
        if result.get('total_marks'):
            print(f"   ✅ Total marks: {result['total_marks']}")
    
    # Add metadata
    result['_metadata'] = {
        'parser_type': 'trained_sectioned',
        'boundaries_used': layout_parser.boundaries if hasattr(layout_parser, 'boundaries') else {}
    }
    
    return result

# Alias for compatibility
parse_sectioned = parse_sectioned_trained
