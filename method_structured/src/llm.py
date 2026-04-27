import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configure Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_with_llm(text):
    """
    Sends OCR text to Groq (Llama 3.1) and extracts structured JSON.
    """
    prompt = f"""
    Extract structured data from the marksheet text provided below.
    Return ONLY valid JSON.
    
    Schema:
    {{
      "student_name": "",
      "mother_name": "",
      "father_name": "",
      "dob": "",
      "school_name": "",
      "unique_id": "",
      "index_no": "",
      "board": "",
      "exam_name": "",
      "year": 2021,
      "subjects": [
        {{
          "code": "",
          "subject": "", 
          "marks": 0.0,
          "grade": "",
          "components": [
             {{"name": "", "marks": 0.0}}
          ]
        }}
      ],
      "internal_assessments": [
        {{"name": "", "grade": ""}}
      ],
      "total": null,
      "percentage": null,
      "result_status": "",
      "result_date": ""
    }}

    Rules:
    - Capture school_name, unique_id, and index_no.
    - LITERAL NAMES: Do NOT split names. Use the exact text for subjects and components (e.g., if it says 'HISTORY CIVICS', use that exact string).
    - MARKS VS GRADES: 'marks' must be numeric. 'grade' is for alphabetical grades (A, B, C) or positional grades. Do NOT put 'Marks in Words' (like 'NINE FIVE') in any field.
    - NESTING: Component marks must match the document. If a mark is missing, use null, NOT 0.0.
    - TOTAL: Only fill 'total' and 'percentage' if they are explicitly labeled as totals on the document. Do NOT guess or reuse subject marks as totals.
    - Return ONLY valid JSON.

    Text:
    {text}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized document parser that outputs strictly valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'
