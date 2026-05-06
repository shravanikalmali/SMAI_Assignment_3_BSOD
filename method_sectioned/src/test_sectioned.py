#!/usr/bin/env python
import sys
from method_sectioned.src.parser import parse_sectioned

if len(sys.argv) < 2:
    print("Usage: python test_sectioned.py <path_to_marksheet>")
    sys.exit(1)

result = parse_sectioned(sys.argv[1], debug=True)

print("\n" + "="*50)
print("FINAL RESULT:")
print("="*50)
import json
print(json.dumps(result, indent=2, default=str))