import json
import logging
from .ocr import extract_text_from_image, extract_text_from_pdf
from .llm import extract_with_llm
from .schema import Marksheet

import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_ocr_text(text):
    """
    Minimizes token count by removing OCR artifacts and redundant whitespace.
    """
    # Remove non-ASCII characters that usually come from background noise
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Remove common OCR artifacts like pipes, underscores used for table lines
    text = re.sub(r'[|_~\\-]{2,}', ' ', text)
    # Collapse multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_document(file_path):
    """
    Complete pipeline: OCR -> LLM -> Validation
    """
    logger.info(f"Processing file: {file_path}")
    
    # 1. OCR
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    if not text:
        return {"error": "No text extracted from document"}

    text = clean_ocr_text(text)

    # 2. LLM Extraction with Retry logic
    raw_output = ""
    data = None
    
    for attempt in range(2):
        logger.info(f"LLM Extraction attempt {attempt + 1}")
        raw_output = extract_with_llm(text)
        
        try:
            # Basic cleanup if LLM still wraps in JSON markdown
            if "```json" in raw_output:
                 raw_output = raw_output.split("```json")[-1].split("```")[0].strip()
            elif "```" in raw_output:
                 raw_output = raw_output.split("```")[-1].split("```")[0].strip()
            
            logger.info(f"RAW LLM OUTPUT: {raw_output[:500]}...")
            data = json.loads(raw_output)
            if "error" not in data:
                break
        except json.JSONDecodeError as je:
            logger.warning(f"Invalid JSON from LLM: {str(je)}")
            continue
    
    if data is None:
        return {"error": "Failed to extract valid JSON from LLM", "raw": raw_output}
    
    if isinstance(data, dict) and "error" in data:
        return {"error": data["error"], "raw": raw_output}

    # 4. Pydantic Validation
    try:
        validated = Marksheet(**data)
        return validated.dict()
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return {"error": "Validation failed", "details": str(e), "data": data}
