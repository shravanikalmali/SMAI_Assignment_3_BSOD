import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configure Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_dynamic(text):
    """
    Open-World Extraction using Groq (Llama 3.1).
    """
    prompt = f"""
    Act as a master document analyst. Extract EVERY piece of information from the marksheet text below.
    
    Guidelines:
    - Create a logical, hierarchical JSON structure.
    - Identify all CORE entities (Student, School, Board, Dates, IDs).
    - Capture all subjects, marks, grades, and sub-components.
    - IGNORE: Notes, remarks, generic footers, council taglines, or overleaf instructions.
    - STRICTLY FOCUS on academic performance and personal identification.
    - Return ONLY valid JSON.
    
    Text:
    {text}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a master document analyst that outputs ONLY valid JSON."
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
