"""
Layout parser using trained model for section detection
"""

import os
import cv2
import numpy as np
import easyocr
import json

class LayoutParserTrained:
    def __init__(self, debug=True):
        self.debug = debug
        self.use_trained_model = False
        
        # Find the boundaries file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        boundaries_path = os.path.join(base_dir, "method_trained_sectioned", "config", "section_boundaries.json")
        
        # Load trained boundaries if exists
        if os.path.exists(boundaries_path):
            with open(boundaries_path, 'r') as f:
                self.boundaries = json.load(f)
            print("✅ Loaded trained section boundaries")
            self.use_trained_model = True
        else:
            # Fallback to rule-based
            self.boundaries = {
                'student_info': {'y_min': 0, 'y_max': 25},
                'subject_table': {'y_min': 25, 'y_max': 65},
                'totals': {'y_min': 65, 'y_max': 85},
                'result': {'y_min': 85, 'y_max': 100}
            }
            print("⚠️ Using fallback rule-based boundaries")
        
        # Initialize EasyOCR
        try:
            self.ocr = easyocr.Reader(['en'], gpu=False)
            print("✅ EasyOCR initialized")
        except Exception as e:
            print(f"❌ Failed to initialize EasyOCR: {e}")
            self.ocr = None
    
    def extract_sections(self, image_path):
        """Extract sections using trained boundaries"""
        
        if self.ocr is None:
            print("❌ EasyOCR not initialized")
            return None
            
        if not os.path.exists(image_path):
            print(f"❌ File not found: {image_path}")
            return None
        
        print(f"\n📄 Processing: {os.path.basename(image_path)}")
        
        # Load image
        img = self._load_image(image_path)
        if img is None:
            return None
        
        img_height, img_width = img.shape[:2]
        print(f"   Image size: {img_width}x{img_height}")
        
        # Run OCR
        print("   Running OCR...")
        result = self.ocr.readtext(img)
        print(f"   ✅ Found {len(result)} text blocks")
        
        # Parse with trained boundaries
        sections = self._parse_with_trained_boundaries(result, img_height)
        
        if self.debug:
            self._print_section_summary(sections)
        
        return sections
    
    def _parse_with_trained_boundaries(self, result, img_height):
        """Parse OCR results using trained section boundaries"""
        
        sections = {
            'student_info': [],
            'subject_table': [],
            'totals': [],
            'result': [],
            'header': [],
            'footer': [],
            'other': []
        }
        
        for item in result:
            try:
                bbox = item[0]
                text = item[1]
                
                if not text or len(text.strip()) < 2:
                    continue
                
                # Get Y position
                y_coords = [p[1] for p in bbox]
                y_min = min(y_coords)
                y_percent = (y_min / img_height) * 100
                
                # Classify using trained boundaries
                section = self._classify_with_boundaries(y_percent)
                sections[section].append(text)
                
            except Exception as e:
                continue
        
        # Convert to strings
        for key in sections:
            if sections[key]:
                sections[key] = '\n'.join(sections[key])
            else:
                sections[key] = ""
        
        sections['full_text'] = '\n'.join([v for v in sections.values() if v])
        
        return sections
    
    def _classify_with_boundaries(self, y_percent):
        """Classify text based on trained boundaries"""
        for section, bounds in self.boundaries.items():
            if bounds['y_min'] <= y_percent < bounds['y_max']:
                return section
        return 'other'
    
    def _load_image(self, image_path):
        """Load image, handling PDFs"""
        if image_path.lower().endswith('.pdf'):
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(image_path, first_page=1, last_page=1)
                if images:
                    img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
                    return img
            except Exception as e:
                print(f"❌ PDF conversion failed: {e}")
                return None
        else:
            img = cv2.imread(image_path)
            return img
    
    def _print_section_summary(self, sections):
        """Print summary"""
        print("\n" + "="*60)
        print("📊 SECTION EXTRACTION (TRAINED MODEL)")
        print("="*60)
        
        for section_name in ['student_info', 'subject_table', 'totals', 'result']:
            text = sections.get(section_name, "")
            if text and len(text.strip()) > 0:
                char_count = len(text)
                preview = text[:100].replace('\n', ' ')
                print(f"\n📁 {section_name.upper()}: {char_count} chars")
                print(f"   Preview: {preview}...")

def extract_sections_from_file(file_path, debug=True):
    """Wrapper function"""
    parser = LayoutParserTrained(debug=debug)
    return parser.extract_sections(file_path)
