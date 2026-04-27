import json
import logging
import re
from .ocr import extract_text_from_image, extract_text_from_pdf
from .llm import extract_dynamic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_ocr_text(text):
    """
    Minimizes token count by removing OCR artifacts and redundant whitespace.
    """
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[|_~\\-]{2,}', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_dynamic(file_path):
    """
    Dynamic Pipeline: OCR -> Dynamic LLM -> Raw JSON
    """
    logger.info(f"Processing file dynamically: {file_path}")
    
    # 1. OCR (Reusing stable OCR logic)
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    if not text:
        return {"error": "No text extracted from document"}

    # Optimization
    text = clean_ocr_text(text)

    # 2. Dynamic Extraction
    raw_output = extract_dynamic(text)
    
    try:
        # Cleanup and Load
        if "```json" in raw_output:
             raw_output = raw_output.split("```json")[-1].split("```")[0].strip()
        elif "```" in raw_output:
             raw_output = raw_output.split("```")[-1].split("```")[0].strip()
        
        logger.info(f"RAW DYNAMIC OUTPUT: {raw_output[:500]}...")
        data = json.loads(raw_output)
        return data
    except Exception as e:
        logger.error(f"Dynamic parse failed: {str(e)}")
        return {"error": "Failed to parse dynamic JSON", "raw": raw_output}
