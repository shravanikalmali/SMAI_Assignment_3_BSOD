"""
Layout-based section detection using PaddleOCR.
This automatically detects different sections like tables, headers, text blocks.
"""

import os
import cv2
import numpy as np
from paddleocr import PaddleOCR
import sys


ocr_instance = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    layout=True,
    show_log=False,
    use_gpu=False
)

class LayoutParser:
    """
    Uses PaddleOCR's layout analysis to detect and extract document sections.
    No training required - uses pre-trained layout model.
    """
    
    def __init__(self, debug=True):
        self.debug = debug
        
        print("\n" + "="*60)
        print("🔄 Using shared PaddleOCR instance...")
        print("="*60)
        
        self.ocr = ocr_instance
        
        print("✅ PaddleOCR ready!\n")


    def extract_sections(self, image_path):
        """
        Extract text from document, grouped by detected layout sections.
        
        Args:
            image_path: Path to the marksheet image/PDF
            
        Returns:
            dict: {
                'student_info': 'text from student info area',
                'subject_table': 'text from marks table',
                'totals': 'text from totals area',
                'result': 'text from result area',
                'header': 'text from header',
                'other': 'remaining text',
                'full_text': 'all text combined'
            }
        """
        if not os.path.exists(image_path):
            print(f"❌ File not found: {image_path}")
            return None
        
        print(f"\n📄 Processing: {os.path.basename(image_path)}")
        
        # Read image to get dimensions
        if image_path.lower().endswith('.pdf'):
            # For PDF, convert first page to image
            from pdf2image import convert_from_path
            images = convert_from_path(image_path, first_page=1, last_page=1)
            if images:
                img = np.array(images[0])
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                print("❌ Could not convert PDF to image")
                return None
        else:
            img = cv2.imread(image_path)
        
        if img is None:
            print(f"❌ Could not read image: {image_path}")
            return None
        
        img_height, img_width = img.shape[:2]
        print(f"   Image size: {img_width}x{img_height}")
        
        # Run OCR with layout detection
        print("   Running OCR with layout detection...")
        result = self.ocr.ocr(image_path, rec=True, layout=True)
        
        # Parse the result
        sections = self._parse_layout_result(result, img_height)
        
        # Print debug info
        if self.debug:
            self._print_section_summary(sections)
        
        return sections
    
    def _parse_layout_result(self, result, img_height):
        """
        Parse PaddleOCR result into meaningful sections.
        
        PaddleOCR layout types can include:
        - 'table': Subject marks table
        - 'header': Top section with title/board info
        - 'footer': Bottom section
        - 'text': Regular text
        - 'title': Document title
        - 'figure': Images/diagrams
        
        We map these to our section types based on content + position.
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
        
        # Check if result has layout information
        # PaddleOCR returns different formats depending on version
        # We'll handle both cases
        
        try:
            # Case 1: Result has layout annotations
            if isinstance(result, list) and len(result) > 0:
                for item in result:
                    self._process_result_item(item, sections, img_height)
            
            # Case 2: Try to access the layout information differently
            elif hasattr(result, 'layout'):
                for layout_block in result.layout:
                    self._process_layout_block(layout_block, sections, img_height)
            
            # Case 3: Fallback - use positional heuristics
            else:
                print("   ⚠️ No layout data found, using positional heuristics...")
                self._fallback_positional_parsing(result, sections, img_height)
        
        except Exception as e:
            print(f"   ⚠️ Layout parsing error: {e}")
            print("   Falling back to positional parsing...")
            self._fallback_positional_parsing(result, sections, img_height)
        
        # Convert lists to single strings
        result_sections = {}
        for key, text_list in sections.items():
            if text_list:
                result_sections[key] = '\n'.join(text_list)
        
        # Add full text
        result_sections['full_text'] = '\n'.join([v for v in result_sections.values()])
        
        return result_sections
    
    def _process_result_item(self, item, sections, img_height):
        """Process a single item from OCR result"""
        try:
            # PaddleOCR often returns: [[bbox], (text, confidence), layout_type]
            if len(item) >= 3:
                bbox = item[0]
                text = item[1][0] if isinstance(item[1], tuple) else item[1]
                layout_type = item[2] if len(item) > 2 else 'text'
                
                # Calculate Y position (percentage from top)
                y_min = min([p[1] for p in bbox]) if bbox else 0
                y_percent = (y_min / img_height) * 100 if img_height > 0 else 50
                
                # Classify based on layout type and content
                section = self._classify_section(text, layout_type, y_percent)
                sections[section].append(text)
                
            # Simple format: [bbox, text, confidence]
            elif len(item) >= 2:
                bbox = item[0]
                text = item[1][0] if isinstance(item[1], tuple) else item[1]
                
                y_min = min([p[1] for p in bbox]) if bbox else 0
                y_percent = (y_min / img_height) * 100 if img_height > 0 else 50
                
                section = self._classify_by_position_and_content(text, y_percent)
                sections[section].append(text)
                
        except Exception as e:
            print(f"   Warning: Could not process item: {e}")
    
    def _process_layout_block(self, layout_block, sections, img_height):
        """Process layout block from PaddleOCR layout analysis"""
        try:
            bbox = layout_block.bbox
            text = layout_block.text
            layout_type = layout_block.type if hasattr(layout_block, 'type') else 'text'
            
            y_min = bbox[1] if len(bbox) > 1 else 0
            y_percent = (y_min / img_height) * 100 if img_height > 0 else 50
            
            section = self._classify_section(text, layout_type, y_percent)
            sections[section].append(text)
            
        except Exception as e:
            print(f"   Warning: Could not process layout block: {e}")
    
    def _classify_section(self, text, layout_type, y_percent):
        """Classify a block into our section types"""
        text_lower = text.lower()
        
        # If layout analysis identified it as a table, it's likely subject marks
        if layout_type == 'table':
            return 'subject_table'
        
        # Header type - top of page
        if layout_type == 'header' or y_percent < 15:
            return 'header'
        
        # Footer type - bottom of page
        if layout_type == 'footer' or y_percent > 85:
            return 'footer'
        
        # Title might contain student info
        if layout_type == 'title':
            if any(kw in text_lower for kw in ['name', 'roll', 'student']):
                return 'student_info'
            return 'header'
        
        # Content-based classification
        # Student info keywords
        student_keywords = ['name:', 'student name', 'roll no', 'registration', 
                           'father', 'mother', 'date of birth', 'dob', 'candidate']
        if any(kw in text_lower for kw in student_keywords):
            return 'student_info'
        
        # Totals keywords
        total_keywords = ['total', 'aggregate', 'obtained', 'grand total', 'out of']
        if any(kw in text_lower for kw in total_keywords):
            return 'totals'
        
        # Result keywords
        result_keywords = ['result:', 'pass', 'fail', 'division', 'percentage', '%']
        if any(kw in text_lower for kw in result_keywords):
            return 'result'
        
        # Table-like content (has numbers and multiple items)
        words = text.split()
        numbers = [w for w in words if w.replace('.', '').isdigit()]
        if layout_type == 'text' and len(numbers) >= 2 and len(words) >= 4:
            return 'subject_table'
        
        return 'other'
    
    def _classify_by_position_and_content(self, text, y_percent):
        """Fallback classification using only position and content"""
        text_lower = text.lower()
        
        # Student info area (top 30% of page)
        if y_percent < 30:
            student_keywords = ['name:', 'roll', 'father', 'mother', 'dob']
            if any(kw in text_lower for kw in student_keywords):
                return 'student_info'
            return 'header'
        
        # Table area (middle 40-70% of page)
        if 30 <= y_percent < 70:
            if any(kw in text_lower for kw in ['math', 'science', 'english', 'hindi']):
                return 'subject_table'
            # Has numbers and multiple words
            words = text.split()
            numbers = [w for w in words if w.replace('.', '').isdigit()]
            if len(numbers) >= 2 and len(words) >= 3:
                return 'subject_table'
            return 'other'
        
        # Bottom area
        if y_percent >= 70:
            if any(kw in text_lower for kw in ['total', 'result', 'percentage']):
                return 'totals' if 'total' in text_lower else 'result'
            return 'footer'
        
        return 'other'
    
    def _fallback_positional_parsing(self, result, sections, img_height):
        """Fallback when layout detection doesn't work"""
        print("   Using position-based section detection...")
        
        # Try to extract as simple OCR list
        try:
            # If result is a list of lists (standard OCR output)
            if isinstance(result, list):
                for line in result:
                    if isinstance(line, list) and len(line) >= 2:
                        # Get text
                        if isinstance(line[1], tuple):
                            text = line[1][0]
                        else:
                            text = line[1]
                        
                        # Get bbox if available
                        if len(line) >= 1 and isinstance(line[0], list):
                            bbox = line[0]
                            y_min = min([p[1] for p in bbox]) if bbox else 0
                        else:
                            y_min = 0
                        
                        y_percent = (y_min / img_height) * 100 if img_height > 0 else 50
                        section = self._classify_by_position_and_content(text, y_percent)
                        sections[section].append(text)
        except Exception as e:
            print(f"   Fallback parsing error: {e}")
    
    def _print_section_summary(self, sections):
        """Print summary of extracted sections"""
        print("\n" + "="*60)
        print("📊 SECTION EXTRACTION SUMMARY")
        print("="*60)
        
        for section_name, text in sections.items():
            if text and section_name != 'full_text':
                char_count = len(text)
                line_count = text.count('\n') + 1
                preview = text[:150].replace('\n', ' ')
                print(f"\n📁 {section_name.upper()}:")
                print(f"   Lines: {line_count}, Characters: {char_count}")
                print(f"   Preview: {preview}...")
        
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