import easyocr
from pypdf import PdfReader
import os

# Initialize EasyOCR reader once
# gpu=False to ensure it works on all systems without CUDA issues
reader_ocr = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(path):
    """
    Extracts text from an image file using EasyOCR.
    """
    if not os.path.exists(path):
        return ""
        
    result = reader_ocr.readtext(path, detail=0)
    return " ".join(result)

def extract_text_from_pdf(path):
    """
    Extracts text from a PDF file using pypdf.
    Falls back to EasyOCR if the PDF is image-based.
    """
    if not os.path.exists(path):
        return ""
        
    text = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    except Exception as e:
        import logging
        logging.warning(f"pypdf failed to read {path}: {str(e)}")
    
    # If no text extracted, it might be a scanned PDF or images
    if len(text.strip()) < 50:
        try:
            from pdf2image import convert_from_path
            import numpy as np
            
            # Convert PDF to images
            images = convert_from_path(path)
            ocr_text = ""
            for img in images:
                # EasyOCR handles PIL images
                result = reader_ocr.readtext(np.array(img), detail=0)
                ocr_text += " ".join(result) + "\n"
            
            if ocr_text.strip():
                return ocr_text.strip()
        except Exception as e:
            import logging
            logging.error(f"PDF OCR Fallback failed: {str(e)}")
        
    return text.strip()
