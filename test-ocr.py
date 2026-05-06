#!/usr/bin/env python
import sys
import json

if len(sys.argv) < 2:
    print("Usage: python test_easyocr_parser.py <path_to_marksheet>")
    print("Example: python test_easyocr_parser.py marksheet.jpg")
    sys.exit(1)

from method_sectioned.src.parser import parse_sectioned

print("Testing Sectioned Parser with EasyOCR...")
result = parse_sectioned(sys.argv[1], debug=True)

print("\n" + "="*50)
print("EXTRACTION RESULTS:")
print("="*50)

# Print only relevant fields
output = {k: v for k, v in result.items() if not k.startswith('_')}
print(json.dumps(output, indent=2, default=str))

print("\n" + "="*50)
print("SUMMARY:")
print("="*50)
print(f"Student Name: {result.get('student_name', 'NOT FOUND')}")
print(f"Subjects Found: {len(result.get('subjects', []))}")
print(f"Total Marks: {result.get('total_marks', 'NOT FOUND')}")
print(f"Percentage: {result.get('percentage', 'NOT FOUND')}")