# 📝 Smart Marksheet Parser

A high-fidelity document extraction pipeline designed for Indian school marksheets (ICSE, ISC, CBSE). This system uses a hybrid approach: **EasyOCR** for text localization and **Groq (Llama 3.3)** for intelligent structured parsing.

## 🚀 Features
- **Dual Pipeline Strategy**:
    - **Structured Parser**: Follows a strict Pydantic contract. Perfect for automation and databases.
    - **Dynamic Parser**: An "Open-World" analyst that adapts its schema to the specific document.
- **Board Agnostic**: Successfully tested against ICSE, ISC, and CBSE formats.
- **Token Optimized**: Built-in sanitization to strip OCR noise and minimize API quota usage.
- **High Speed**: Powered by Groq's LPUs (Llama 3.3 70B).

## 🛠 Setup & Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_key_here
   ```
3. **System Requirements**: 
   Ensure `poppler-utils` is installed on your OS (required for PDF processing).

## 🏃‍♂️ How to Run

### 1. Structured Pipeline (Standard)
Best for production use where you need consistent keys.
```bash
streamlit run app.py
```
*Access at: http://localhost:8501*

### 2. Dynamic Pipeline (Alpha)
Best for exploratory analysis and capturing every single detail/note.
```bash
streamlit run app_dynamic.py --server.port 8502
```
*Access at: http://localhost:8502*

## 🏗 Project Structure
- `src/`: Core logic, Pydantic schemas, and structured LLM prompts.
- `src_dynamic/`: Adaptive parser logic without fixed schemas.
- `data/raw/`: Place your test marksheets here.
- `diag_api.py`: Utility to verify available models and API status.

## ⚖️ Schema Details
The structured output includes:
- **Personal Metadata**: Name, Parents, DOB, Unique IDs.
- **Academic Table**: Subject Codes, Marks, Alphabetical/Positional Grades.
- **Hierarchical Components**: Support for nested marks (e.g., Theory/Practical or Lang/Lit).
- **Internal Assessments**: Graded subjects like SUPW.
- **Result Info**: Pass/Fail status and Declaration Date.
