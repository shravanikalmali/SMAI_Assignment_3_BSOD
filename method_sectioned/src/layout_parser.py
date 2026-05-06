"""
Layout-based section detection using EasyOCR.
More stable than PaddleOCR for this use case.
"""

import os
import cv2
import numpy as np
import easyocr
import re

class LayoutParser:
    """
    Uses EasyOCR to extract text and applies positional heuristics
    to identify document sections.
    """
    
    def __init__(self, debug=True):
        self.debug = debug
        
        if self.debug:
            print("\n" + "="*60)
            print("🔄 Initializing Layout Parser (EasyOCR-based)")
            print("="*60)
        
        # Initialize EasyOCR
        try:
            self.ocr = easyocr.Reader(['en'], gpu=False)
            print("✅ EasyOCR initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize EasyOCR: {e}")
            self.ocr = None

    def extract_sections(self, image_path):
        """
        Extract text from document, grouped by position-based sections.
        
        Args:
            image_path: Path to the marksheet image/PDF
            
        Returns:
            dict: {
                'student_info': 'text from student info area',
                'subject_table': 'text from marks table',
                'totals': 'text from totals area',
                'result': 'text from result area',
                'header': 'text from header',
                'footer': 'text from footer',
                'other': 'remaining text',
                'full_text': 'all text combined'
            }
        """
        if self.ocr is None:
            print("❌ EasyOCR not initialized.")
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
        print("   Running OCR with EasyOCR...")
        try:
            # EasyOCR returns: [([[x1,y1],[x2,y2],[x3,y3],[x4,y4]], text, confidence), ...]
            result = self.ocr.readtext(img)
            print(f"   ✅ OCR found {len(result)} text blocks")
        except Exception as e:
            print(f"   ❌ OCR failed: {e}")
            return None
        
        # Parse OCR results with position-based classification
        sections = self._parse_ocr_by_position(result, img_height)
        
        # Print debug info
        if self.debug:
            self._print_section_summary(sections)
        
        return sections
    
    def _load_image(self, image_path):
        """Load image from path, handling PDFs"""
        if image_path.lower().endswith('.pdf'):
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(image_path, first_page=1, last_page=1)
                if images:
                    # Convert PIL image to numpy array for OpenCV
                    img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
                    return img
                else:
                    print("❌ Could not convert PDF to image")
                    return None
            except ImportError:
                print("❌ pdf2image not installed. Install with: pip install pdf2image")
                return None
            except Exception as e:
                print(f"❌ PDF conversion failed: {e}")
                return None
        else:
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Could not read image: {image_path}")
            return img
    
    def _parse_ocr_by_position(self, result, img_height):
        """
        Parse OCR results and classify text blocks by their Y-position on the page.
        """
        sections = {
            'student_info': [],
            'subject_table': [],
            'totals': [],
            'result': [],
            'header': [],
            'footer': [],
            'other': []
        }
        
        if not result:
            print("   ⚠️ No OCR results found")
            return sections
        
        print(f"   Classifying {len(result)} text blocks by position...")
        
        valid_blocks = 0
        for item in result:
            try:
                # EasyOCR format: (bbox, text, confidence)
                if len(item) >= 2:
                    bbox = item[0]  # List of 4 points
                    text = item[1]   # String
                    
                    if not text or len(text.strip()) < 2:
                        continue
                    
                    valid_blocks += 1
                    
                    # Get Y position (top of bounding box)
                    y_coords = [p[1] for p in bbox]
                    y_min = min(y_coords)
                    
                    # Calculate position percentage from top
                    y_percent = (y_min / img_height) * 100 if img_height > 0 else 50
                    
                    # Classify based on position and content
                    section = self._classify_text_block(text, y_percent)
                    sections[section].append(text)
                    
            except Exception as e:
                if self.debug:
                    print(f"   Debug: Could not process item: {e}")
                continue
        
        print(f"   Successfully processed {valid_blocks} text blocks")
        
        # Convert lists to strings
        for key in sections:
            if sections[key]:
                sections[key] = '\n'.join(sections[key])
            else:
                sections[key] = ""
        
        # Add full text
        sections['full_text'] = '\n'.join([v for v in sections.values() if v])
        
        return sections
    
    def _classify_text_block(self, text, y_percent):
        """
        Classify a text block into a section based on position and keywords.
        """
        if not text:
            return 'other'
        
        text_lower = text.lower()
        
        # TOP SECTION (0-25%): Header and Student Info
        if y_percent < 25:
            # Student info keywords
            student_keywords = [
                'name:', 'student name', "student's name", 'roll no', 'roll number',
                'registration', 'register no', 'father', 'mother', 'parent',
                'date of birth', 'dob', 'candidate', 'applicant'
            ]
            
            if any(kw in text_lower for kw in student_keywords):
                return 'student_info'
            
            # Board/School header
            header_keywords = ['board', 'school', 'examination', 'secondary', 'higher secondary', 'council']
            if any(kw in text_lower for kw in header_keywords):
                return 'header'
            
            return 'header'
        
        # MIDDLE SECTION (25-65%): Subject Table Area
        elif 25 <= y_percent < 65:
            # Strong indicators of subject table
            subject_keywords = [
                'math', 'science', 'english', 'hindi', 'physics', 'chemistry',
                'biology', 'history', 'geography', 'economics', 'accounts',
                'computer', 'physical education', 'art', 'music', 'civics'
            ]
            
            # Check for subject names
            if any(kw in text_lower for kw in subject_keywords):
                return 'subject_table'
            
            # Check if it looks like table data (has numbers and multiple words)
            words = text.split()
            numbers = [w for w in words if w.replace('.', '').replace('-', '').replace('/', '').isdigit()]
            
            if len(numbers) >= 2 and len(words) >= 4:
                return 'subject_table'
            
            return 'other'
        
        # BOTTOM SECTION (65-100%): Totals and Results
        else:
            # Total marks keywords
            total_keywords = ['total', 'aggregate', 'grand total', 'sum', 'obtained', 'out of']
            if any(kw in text_lower for kw in total_keywords):
                return 'totals'
            
            # Result keywords
            result_keywords = [
                'result', 'pass', 'fail', 'division', 'percentage', '%',
                'grade', 'cgpa', 'gpa', 'merit', 'rank'
            ]
            if any(kw in text_lower for kw in result_keywords):
                return 'result'
            
            return 'footer'
    
    def _print_section_summary(self, sections):
        """Print summary of extracted sections"""
        print("\n" + "="*60)
        print("📊 SECTION EXTRACTION SUMMARY (EasyOCR)")
        print("="*60)
        
        for section_name in ['header', 'student_info', 'subject_table', 'totals', 'result', 'footer', 'other']:
            text = sections.get(section_name, "")
            if text and len(text.strip()) > 0:
                char_count = len(text)
                line_count = text.count('\n') + 1
                preview = text[:150].replace('\n', ' ')
                print(f"\n📁 {section_name.upper()}:")
                print(f"   Lines: {line_count}, Characters: {char_count}")
                print(f"   Preview: {preview}...")
        
        # Check which sections have content
        non_empty = [k for k, v in sections.items() if v and len(v.strip()) > 0 and k != 'full_text']
        empty = [k for k, v in sections.items() if (not v or len(v.strip()) == 0) and k != 'full_text']
        
        print(f"\n✅ Non-empty sections: {', '.join(non_empty) if non_empty else 'None'}")
        if empty:
            print(f"⚠️ Empty sections: {', '.join(empty)}")
        
        print("\n" + "="*60 + "\n")


# Utility function for easy use
def extract_sections_from_file(file_path, debug=True):
    """
    Simple wrapper to extract sections from a file.
    
    Args:
        file_path: Path to marksheet image or PDF
        debug: Print debug information
    
    Returns:
        dict with sections
    """
    parser = LayoutParser(debug=debug)
    return parser.extract_sections(file_path)