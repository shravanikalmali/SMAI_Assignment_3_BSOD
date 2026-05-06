#!/usr/bin/env python3
"""
Training script for marksheet section detector
"""

import os
import sys
import cv2
import numpy as np
import json
from collections import defaultdict
import easyocr
import glob
from datetime import datetime

# Use absolute path - YOUR DATA IS IN data/raw/training_data
BASE_DIR = "/home/popos/3-2/SMAI/Assignments/Ass3/SMAI_Assignment_3_BSOD"
TRAINING_DIR = os.path.join(BASE_DIR, "data", "raw", "training_data")

print("="*70)
print("🎯 TRAINING SECTION DETECTOR")
print("="*70)
print(f"📁 Training data path: {TRAINING_DIR}")

# Check if training directory exists
if not os.path.exists(TRAINING_DIR):
    print(f"❌ Training directory not found: {TRAINING_DIR}")
    print("\nTrying alternative paths...")
    
    # Try alternative paths
    alternatives = [
        os.path.join(BASE_DIR, "data", "training_data"),
        os.path.join(BASE_DIR, "training_data"),
        os.path.join(BASE_DIR, "data", "raw", "training_data")
    ]
    
    for alt in alternatives:
        if os.path.exists(alt):
            TRAINING_DIR = alt
            print(f"✅ Found training data at: {TRAINING_DIR}")
            break
    else:
        print("❌ Could not find training data!")
        sys.exit(1)

# List files in training directory
files = os.listdir(TRAINING_DIR)
print(f"\n📸 Found {len(files)} files in training_data:")

# Get all image files
image_paths = []
for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
    image_paths.extend(glob.glob(os.path.join(TRAINING_DIR, ext)))

print(f"📊 Found {len(image_paths)} valid training images")

if len(image_paths) == 0:
    print("❌ No images found! Please check your files.")
    sys.exit(1)

# Show first 5 files
print("\n📋 Training files:")
for f in image_paths[:5]:
    print(f"   - {os.path.basename(f)}")
if len(image_paths) > 5:
    print(f"   ... and {len(image_paths)-5} more")

# Initialize EasyOCR
print("\n🔄 Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)
print("✅ EasyOCR ready")

# Analyze each image
all_y_positions = defaultdict(list)
text_examples = defaultdict(list)

print("\n📌 Analyzing marksheets...")
for idx, img_path in enumerate(image_paths, 1):
    print(f"Processing {idx}/{len(image_paths)}: {os.path.basename(img_path)}")
    
    # Load image
    if img_path.lower().endswith('.pdf'):
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(img_path, first_page=1, last_page=1)
            if images:
                img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
            else:
                print(f"   ⚠️ Could not convert PDF")
                continue
        except Exception as e:
            print(f"   ⚠️ PDF conversion failed: {e}")
            continue
    else:
        img = cv2.imread(img_path)
        if img is None:
            print(f"   ⚠️ Could not read image")
            continue
    
    height = img.shape[0]
    result = reader.readtext(img)
    print(f"   Found {len(result)} text blocks")
    
    for item in result:
        bbox = item[0]
        text = item[1]
        confidence = item[2]
        
        if confidence < 0.5 or len(text) < 2:
            continue
        
        # Get Y position
        y_coords = [p[1] for p in bbox]
        y_center = sum(y_coords) / len(y_coords)
        y_percent = (y_center / height) * 100
        
        # Categorize text
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['name:', 'student', 'roll no', 'father', 'mother', 'dob', 'candidate']):
            text_type = 'student_info'
        elif any(kw in text_lower for kw in ['math', 'science', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography']):
            text_type = 'subject'
        elif any(kw in text_lower for kw in ['total', 'aggregate', 'obtained', 'out of']):
            text_type = 'total'
        elif any(kw in text_lower for kw in ['result', 'pass', 'fail', 'percentage', '%', 'division']):
            text_type = 'result'
        else:
            text_type = 'other'
        
        if text_type != 'other':
            all_y_positions[text_type].append(y_percent)
            if len(text_examples[text_type]) < 3:
                text_examples[text_type].append(text)

# Print results
print("\n" + "="*70)
print("📊 ANALYSIS RESULTS")
print("="*70)

final_boundaries = {}

# Define section mapping
section_mapping = {
    'student_info': ('student_info', 'Student Information'),
    'subject': ('subject_table', 'Subject Marks'),
    'total': ('totals', 'Total Marks'),
    'result': ('result', 'Result Section')
}

for section, (boundary_key, display_name) in section_mapping.items():
    positions = all_y_positions.get(section, [])
    
    if len(positions) >= 5:
        p5 = np.percentile(positions, 5)
        p10 = np.percentile(positions, 10)
        p25 = np.percentile(positions, 25)
        p50 = np.percentile(positions, 50)
        p75 = np.percentile(positions, 75)
        p90 = np.percentile(positions, 90)
        p95 = np.percentile(positions, 95)
        
        print(f"\n📌 {display_name}:")
        print(f"   Samples: {len(positions)}")
        print(f"   Range (10-90%): {p10:.1f}% - {p90:.1f}%")
        print(f"   Median: {p50:.1f}%")
        print(f"   Confidence: ±{np.std(positions):.1f}%")
        
        if text_examples.get(section):
            print(f"   Example: \"{text_examples[section][0][:50]}...\"")
        
        # Store boundary
        if section == 'student_info':
            final_boundaries[boundary_key] = {'y_min': 0, 'y_max': round(p90, 1)}
        elif section == 'subject':
            final_boundaries[boundary_key] = {'y_min': round(p10, 1), 'y_max': round(p90, 1)}
        elif section == 'total':
            final_boundaries[boundary_key] = {'y_min': round(p10, 1), 'y_max': round(p90, 1)}
        elif section == 'result':
            final_boundaries[boundary_key] = {'y_min': round(p10, 1), 'y_max': 100}
    else:
        print(f"\n⚠️ {display_name}: Only {len(positions)} samples (need 5+)")
        print(f"   Using default values")
        
        # Default values
        if section == 'student_info':
            final_boundaries['student_info'] = {'y_min': 0, 'y_max': 25}
        elif section == 'subject':
            final_boundaries['subject_table'] = {'y_min': 25, 'y_max': 65}
        elif section == 'total':
            final_boundaries['totals'] = {'y_min': 65, 'y_max': 85}
        elif section == 'result':
            final_boundaries['result'] = {'y_min': 85, 'y_max': 100}

# Save boundaries
config_dir = os.path.join(BASE_DIR, "method_trained_sectioned", "config")
os.makedirs(config_dir, exist_ok=True)
boundaries_path = os.path.join(config_dir, "section_boundaries.json")

with open(boundaries_path, 'w') as f:
    json.dump(final_boundaries, f, indent=2)

print("\n" + "="*70)
print("📊 FINAL LEARNED BOUNDARIES")
print("="*70)
for section, bounds in final_boundaries.items():
    print(f"   {section:15} : {bounds['y_min']:.1f}% - {bounds['y_max']:.1f}%")

print(f"\n✅ Boundaries saved to: {boundaries_path}")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE!")
print("="*70)
print("\n🎉 Success! Now run: streamlit run app.py")