#!/usr/bin/env python3
"""
Training script for marksheet section detector with detailed output
Includes +-10% expansion on final boundaries
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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SimpleSectionDetector:
    def __init__(self):
        print("Initializing EasyOCR...")
        self.ocr = easyocr.Reader(['en'], gpu=False)
        print("✅ EasyOCR ready")
        
    def extract_features_from_image(self, image_path):
        """Extract features from a marksheet"""
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        height, width = img.shape[:2]
        
        # Run OCR
        result = self.ocr.readtext(img)
        
        # Collect text blocks with positions
        blocks = []
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
            
            # Categorize text type
            text_type = self._categorize_text(text.lower())
            
            blocks.append({
                'y': y_percent,
                'text_type': text_type,
                'text': text[:30],
                'confidence': confidence
            })
        
        return blocks, height
    
    def _categorize_text(self, text_lower):
        """Categorize text based on content"""
        if any(kw in text_lower for kw in ['name:', 'student', 'roll no', 'father', 'mother', 'dob', 'candidate']):
            return 'student_info'
        elif any(kw in text_lower for kw in ['math', 'science', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography']):
            return 'subject'
        elif any(kw in text_lower for kw in ['total', 'aggregate', 'obtained', 'out of']):
            return 'total'
        elif any(kw in text_lower for kw in ['result', 'pass', 'fail', 'percentage', '%', 'division']):
            return 'result'
        else:
            return 'other'
    
    def find_section_boundaries(self, training_dir):
        """Find section boundaries using statistics"""
        
        # Get all image files
        image_paths = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
            image_paths.extend(glob.glob(os.path.join(training_dir, ext)))
        
        print(f"\n📊 Found {len(image_paths)} training images")
        
        if len(image_paths) == 0:
            print(f"❌ No images found in {training_dir}")
            return None
        
        all_y_positions = defaultdict(list)
        text_examples = defaultdict(list)
        
        # Extract data from all images
        for idx, img_path in enumerate(image_paths, 1):
            print(f"Processing {idx}/{len(image_paths)}: {os.path.basename(img_path)}")
            blocks, height = self.extract_features_from_image(img_path)
            
            if not blocks:
                print(f"   ⚠️ No text blocks found")
                continue
                
            # Group by text type
            for block in blocks:
                text_type = block['text_type']
                if text_type != 'other':
                    all_y_positions[text_type].append(block['y'])
                    if len(text_examples[text_type]) < 3:
                        text_examples[text_type].append(block['text'])
        
        # Print statistics
        print("\n" + "="*70)
        print("📊 TEXT BLOCK STATISTICS")
        print("="*70)
        for text_type, positions in all_y_positions.items():
            print(f"\n📌 {text_type.upper()}:")
            print(f"   Total blocks found: {len(positions)}")
            print(f"   Y-position range: {min(positions):.1f}% - {max(positions):.1f}%")
            print(f"   Average Y: {np.mean(positions):.1f}%")
            print(f"   Std deviation: {np.std(positions):.1f}%")
            if text_examples[text_type]:
                print(f"   Example text: {text_examples[text_type][0]}")
        
        # Find boundaries for each section
        boundaries = {}
        
        print("\n" + "="*70)
        print("🎯 AI-DETECTED SECTION PATTERNS")
        print("="*70)
        
        section_order = ['student_info', 'subject', 'total', 'result']
        section_names = {
            'student_info': 'Student Information',
            'subject': 'Subject Marks Table',
            'total': 'Total Marks Section',
            'result': 'Result Section'
        }
        
        for section in section_order:
            if all_y_positions.get(section) and len(all_y_positions[section]) > 5:
                positions = np.array(all_y_positions[section])
                
                # Calculate percentiles
                p5 = np.percentile(positions, 5)
                p10 = np.percentile(positions, 10)
                p25 = np.percentile(positions, 25)
                p50 = np.percentile(positions, 50)
                p75 = np.percentile(positions, 75)
                p90 = np.percentile(positions, 90)
                p95 = np.percentile(positions, 95)
                
                boundaries[section] = {
                    'y_min': float(p10),
                    'y_max': float(p90),
                    'mean_y': float(np.mean(positions)),
                    'median_y': float(p50),
                    'std_y': float(np.std(positions)),
                    'sample_count': len(positions),
                    'percentiles': {
                        '5%': float(p5),
                        '10%': float(p10),
                        '25%': float(p25),
                        '50%': float(p50),
                        '75%': float(p75),
                        '90%': float(p90),
                        '95%': float(p95)
                    }
                }
                
                print(f"\n📌 {section_names[section]}:")
                print(f"   📍 Raw range: {p10:.1f}% - {p90:.1f}% of page")
                print(f"   📊 Median position: {p50:.1f}%")
                print(f"   📈 Confidence (std): ±{np.std(positions):.1f}%")
                print(f"   🔢 Sample size: {len(positions)} text blocks")
                
            else:
                print(f"\n⚠️ Not enough data for {section_names[section]}")
                print(f"   Found {len(all_y_positions.get(section, []))} blocks (need at least 6)")
                # Use default values
                if section == 'student_info':
                    boundaries[section] = {'y_min': 0, 'y_max': 25, 'mean_y': 15}
                elif section == 'subject':
                    boundaries[section] = {'y_min': 30, 'y_max': 65, 'mean_y': 45}
                elif section == 'total':
                    boundaries[section] = {'y_min': 68, 'y_max': 85, 'mean_y': 75}
                elif section == 'result':
                    boundaries[section] = {'y_min': 85, 'y_max': 100, 'mean_y': 92}
                print(f"   Using default values: {boundaries[section]['y_min']:.0f}%-{boundaries[section]['y_max']:.0f}%")
        
        # Create final section mapping with +-10% expansion
        final_boundaries = self._create_section_mapping_with_expansion(boundaries)
        
        return final_boundaries, boundaries
    
    def _create_section_mapping_with_expansion(self, boundaries):
        """
        Convert detected clusters to final section boundaries with +-10% expansion
        """
        
        final_boundaries = {}
        
        # Calculate range sizes and add 10% expansion
        for section, bounds in boundaries.items():
            range_size = bounds['y_max'] - bounds['y_min']
            expand_amount = range_size * 0.10  # 10% expansion
            
            if section == 'student_info':
                # Student info starts at top, only expand downwards
                final_boundaries['student_info'] = {
                    'y_min': 0,
                    'y_max': min(100, bounds['y_max'] + expand_amount)
                }
            elif section == 'subject':
                # Subject table expands both ways
                final_boundaries['subject_table'] = {
                    'y_min': max(0, bounds['y_min'] - expand_amount),
                    'y_max': min(100, bounds['y_max'] + expand_amount)
                }
            elif section == 'total':
                # Totals expands both ways
                final_boundaries['totals'] = {
                    'y_min': max(0, bounds['y_min'] - expand_amount),
                    'y_max': min(100, bounds['y_max'] + expand_amount)
                }
            elif section == 'result':
                # Result goes to bottom, only expand upwards
                final_boundaries['result'] = {
                    'y_min': max(0, bounds['y_min'] - expand_amount),
                    'y_max': 100
                }
        
        # Ensure all sections exist (fallback if missing)
        if 'student_info' not in final_boundaries:
            final_boundaries['student_info'] = {'y_min': 0, 'y_max': 30}
        if 'subject_table' not in final_boundaries:
            final_boundaries['subject_table'] = {'y_min': 25, 'y_max': 70}
        if 'totals' not in final_boundaries:
            final_boundaries['totals'] = {'y_min': 60, 'y_max': 85}
        if 'result' not in final_boundaries:
            final_boundaries['result'] = {'y_min': 80, 'y_max': 100}
        
        return final_boundaries
    
    def save_boundaries(self, boundaries, raw_boundaries, boundaries_path, raw_path):
        """Save boundaries to file"""
        os.makedirs(os.path.dirname(boundaries_path), exist_ok=True)
        
        # Save final boundaries
        with open(boundaries_path, 'w') as f:
            json.dump(boundaries, f, indent=2)
        
        # Save detailed raw boundaries for analysis
        with open(raw_path, 'w') as f:
            json.dump(raw_boundaries, f, indent=2)
        
        print(f"\n✅ Final boundaries (expanded +10%) saved to: {boundaries_path}")
        print(f"✅ Detailed analysis saved to: {raw_path}")

def visualize_boundaries(boundaries, output_path="method_trained_sectioned/config/boundary_visualization.txt"):
    """Create a text visualization of the boundaries"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("SECTION BOUNDARY VISUALIZATION (Expanded +10%)\n")
        f.write("="*70 + "\n\n")
        
        f.write("Page Layout (Top to Bottom):\n")
        f.write("-"*70 + "\n\n")
        
        for section, bounds in boundaries.items():
            y_min = bounds['y_min']
            y_max = bounds['y_max']
            height = y_max - y_min
            
            bar_length = int(height)
            bar = "█" * bar_length
            
            f.write(f"{section.upper()}:\n")
            f.write(f"  Position: {y_min:.1f}% to {y_max:.1f}% of page\n")
            f.write(f"  Height: {height:.1f}% of page\n")
            f.write(f"  Visual: {bar}\n\n")
        
        f.write("-"*70 + "\n")
        f.write("Legend:\n")
        f.write("  █ = Section occupies this percentage of page height\n")
        f.write("\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def main():
    """Main training function"""
    
    print("="*70)
    print("🎯 TRAINING SECTION DETECTOR WITH +-10% EXPANSION")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get the base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    training_dir = os.path.join(base_dir, "data", "training_data")
    
    print(f"\n📁 Base directory: {base_dir}")
    print(f"📁 Training data path: {training_dir}")
    
    # Check if training directory exists
    if not os.path.exists(training_dir):
        print(f"❌ Training directory not found: {training_dir}")
        return None
    
    # List files in training directory
    files = os.listdir(training_dir)
    print(f"\n📸 Files in training_data: {len(files)}")
    
    # Count by type
    images = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))]
    pdfs = [f for f in files if f.endswith('.pdf')]
    print(f"   Images: {len(images)}")
    print(f"   PDFs: {len(pdfs)}")
    
    if len(images) + len(pdfs) == 0:
        print("❌ No valid training files found!")
        return None
    
    # Create directories for saving model
    model_dir = os.path.join(base_dir, "method_trained_sectioned", "models")
    config_dir = os.path.join(base_dir, "method_trained_sectioned", "config")
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    # Initialize detector
    detector = SimpleSectionDetector()
    
    # Find section boundaries
    print("\n📌 Analyzing marksheets to find section patterns...")
    final_boundaries, raw_boundaries = detector.find_section_boundaries(training_dir)
    
    if not final_boundaries:
        print("❌ Could not detect section boundaries")
        return None
    
    # Save boundaries
    boundaries_path = os.path.join(config_dir, "section_boundaries.json")
    raw_path = os.path.join(config_dir, "raw_boundaries_analysis.json")
    detector.save_boundaries(final_boundaries, raw_boundaries, boundaries_path, raw_path)
    
    # Create visualization
    visualize_boundaries(final_boundaries)
    
    print("\n" + "="*70)
    print("📊 FINAL TRAINING SUMMARY (EXPANDED +10%)")
    print("="*70)
    print("🎯 Learned & Expanded Section Boundaries:")
    print("-" * 50)
    for section, bounds in final_boundaries.items():
        print(f"   {section:15} : {bounds['y_min']:5.1f}% - {bounds['y_max']:5.1f}% of page")
    
    print("\n📁 Output files created:")
    print(f"   • {boundaries_path}")
    print(f"   • {raw_path}")
    print(f"   • method_trained_sectioned/config/boundary_visualization.txt")
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return final_boundaries

if __name__ == "__main__":
    boundaries = main()
    
    if boundaries:
        print("\n🎉 Success! The trained model is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Run: streamlit run app.py")
        print("   2. Upload a marksheet to test the 4th method")
        print("\n💡 Note: Boundaries were expanded by +-10% to capture more text")
    else:
        print("\n❌ Training failed.")
        print("\nPlease check:")
        print("   1. Your marksheets are in 'data/training_data/' folder")
        print("   2. Files are .jpg, .png, or .pdf format")
        print("   3. Images are clear and readable")