# 📊 Smart Marksheet Parser: Comparative Extraction Pipeline

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Powered%20By-Groq-orange.svg)](https://groq.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)

A premium, high-fidelity document extraction engine specifically engineered for Indian educational marksheets (CBSE, ICSE, ISC). This system leverages **EasyOCR** for precise spatial text localization and **Groq Cloud (Llama 3.3 70B)** for intelligent, context-aware structured parsing.

---

## ✨ Key Features

- **⚡ Dual-Engine Extraction**: Run two distinct methodologies side-by-side to compare accuracy and depth.
- **🎯 Structured Parser**: Uses strict Pydantic schemas to ensure data integrity. Ideal for automated database ingestion.
- **🧠 Dynamic Parser**: An adaptable "Open-World" analyst that discovers fields on-the-fly, capturing unique nuances of varied document formats.
- **📄 Format Agnostic**: Seamlessly processes PDF and Image formats for all major Indian boards.
- **📉 Token Optimized**: Advanced pre-processing strips OCR artifacts and noise, ensuring maximum efficiency and minimal LLM latency.
- **💾 Multi-Format Export**: One-click export of extracted data into clean **JSON** or flattened **CSV** formats.

---

## 🏗 Project Architecture

```text
marksheet-parser/
├── app.py                      # Main Streamlit Dashboard (Dual-Method Runner)
├── method_structured/          # Strict schema-based extraction logic
│   └── src/parser.py           # Pydantic-validated parsing engine
├── method_dynamic/             # Adaptive, schema-less extraction logic
│   └── src/parser.py           # Zero-shot field discovery engine
├── data/                       # Local storage for raw and processed documents
├── requirements.txt            # Project dependencies
└── .env                        # Environment configuration (API Keys)
```

---

## 🛠 Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.9+ and `poppler-utils` (for PDF processing) installed on your system.
```bash
# For Ubuntu/Debian
sudo apt-get install poppler-utils
```

### 2. Clone & Install
```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory and add your Groq API Key:
```env
GROQ_API_KEY=gsk_your_api_key_here
```

---

## 🏃‍♂️ Getting Started

Launch the comparative dashboard with a single command:

```bash
streamlit run app.py
```

Once running, simply upload your marksheet. The system will automatically:
1. Perform OCR and spatial analysis.
2. Trigger the **Structured** and **Dynamic** LLM pipelines in parallel.
3. Present a side-by-side comparison with instant export options.

---

## 🔬 Methodology Comparison

| Feature | Structured Method | Dynamic Method |
| :--- | :--- | :--- |
| **Logic** | Validated Pydantic Schema | Zero-shot Schema Discovery |
| **Best For** | Production Systems & DBs | Research & Complex Layouts |
| **Flexibility** | High (handles board variations) | Extreme (handles unknown formats) |
| **Output Type** | Predicted JSON Keys | Adaptive JSON Keys |

---

## ⚖️ Extraction Scope

The engine is tuned to capture:
- **Identity**: Student name, Parents, Registration Numbers, DOB.
- **Institutional**: School details, Board name, Year of Exam.
- **Academic**: Subject-wise Theory/Practical marks, Internal Assessments (SUPW), Positional Grades.
- **Results**: Final status, total marks, and declaration dates.

---
*Developed with focus on accuracy and speed using Llama 3-series models on Groq LPUs.*
