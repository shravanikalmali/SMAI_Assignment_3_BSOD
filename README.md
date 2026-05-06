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
├── app.py                      # Main Streamlit Dashboard (multi-method runner)
├── method_structured/          # Strict schema-based extraction logic
│   └── src/parser.py           # Pydantic-validated parsing engine
├── method_dynamic/             # Adaptive, schema-less extraction logic
│   └── src/parser.py           # Zero-shot field discovery engine
├── method_sectioned/           # Heuristic section detection + focused LLM
│   └── src/parser.py
├── method_trained_sectioned/   # Trained boundary section detection + LLM
│   └── src/train_section_detector.py
├── data/                       # Local storage for raw/processed/training data
├── requirements.txt            # Project dependencies
├── setup.sh                    # One-shot setup + run helpers
└── .env                        # Environment configuration (API Keys)
```

---

## 🗂 Complete File Structure

> Excludes `.git/`, `venv/`, and `__pycache__/` artifacts.

```text
.
./app.py
./data
./data/ground_truth
./data/ground_truth/sample_0.json
./data/ground_truth/sample_10.json
./data/ground_truth/sample_11.json
./data/ground_truth/sample_12.json
./data/ground_truth/sample_13.json
./data/ground_truth/sample_14.json
./data/ground_truth/sample_1.json
./data/ground_truth/sample_2.json
./data/ground_truth/sample_3.json
./data/ground_truth/sample_4.json
./data/ground_truth/sample_5.json
./data/ground_truth/sample_6.json
./data/ground_truth/sample_7.json
./data/ground_truth/sample_8.json
./data/ground_truth/sample_9.json
./data/raw
./data/raw/12 marksheet.pdf
./data/raw/in.gov.cbse-HSCER-186053002023.pdf
./data/raw/X marksheet Ahana.pdf
./data/synthetic
./data/synthetic/sample_0.jpg
./data/synthetic/sample_10.jpg
./data/synthetic/sample_11.jpg
./data/synthetic/sample_12.jpg
./data/synthetic/sample_13.jpg
./data/synthetic/sample_14.jpg
./data/synthetic/sample_1.jpg
./data/synthetic/sample_2.jpg
./data/synthetic/sample_3.jpg
./data/synthetic/sample_4.jpg
./data/synthetic/sample_5.jpg
./data/synthetic/sample_6.jpg
./data/synthetic/sample_7.jpg
./data/synthetic/sample_8.jpg
./data/synthetic/sample_9.jpg
./data/testing_data
./data/testing_data/AdityaKumarSharma_CBSE.png
./data/testing_data/NilanjanaDe_CBSE_2.jpeg
./data/testing_data/NilanjanaDe_CBSE_3.jpeg
./data/testing_data/NilanjanaDe_CBSE_4.jpeg
./data/testing_data/NilanjanaDe_CBSE_5.jpeg
./data/testing_data/NilanjanaDe_CBSE_6.jpeg
./data/testing_data/NilanjanaDe_CBSE.jpeg
./data/testing_data/SaloniGoyal_CBSE_2.png
./data/training_data
./data/training_data/AdityaMenon_CBSE.png
./data/training_data/AhanaTalukdar_ICSE.png
./data/training_data/AnitaTalukdar_CBSE.png
./data/training_data/AnjaliSharma_ICSE.png
./data/training_data/AshaWaykole_CBSE.png
./data/training_data/AyeshaJain_CBSE.png
./data/training_data/AyushRameshKhan_CBSE.png
./data/training_data/DiyaKapoor_CBSE.png
./data/training_data/IshaKaur_CBSE.png
./data/training_data/KavitaSinghania_ICSE.png
./data/training_data/KrishnaBalan_CBSE.png
./data/training_data/KritiDutta_CBSE.png
./data/training_data/NanditaSingh_CBSE.png
./data/training_data/NeelamGupta_ICSE.png
./data/training_data/NeetaPatel_CBSE.png
./data/training_data/PriyankaSingh_CBSE.png
./data/training_data/PriyanshiGupta_CBSE(1).jpeg
./data/training_data/PriyanshiGupta_CBSE.jpeg
./data/training_data/PunamKumar_CBSE.png
./data/training_data/RahulMondal_CBSE.png
./data/training_data/SaloniGoyal_CBSE.png
./data/training_data/SanthoshGupta_CBSE.png
./data/training_data/ShreeyashPramodPadale_CBSE.png
./data/training_data/VikramSingh_ICSE.png
./.env
./.gitignore
./method_dynamic
./method_dynamic/__init__.py
./method_dynamic/src
./method_dynamic/src/__init__.py
./method_dynamic/src/llm.py
./method_dynamic/src/ocr.py
./method_dynamic/src/parser.py
./method_sectioned
./method_sectioned/src
./method_sectioned/src/__init__.py
./method_sectioned/src/layout_parser.py
./method_sectioned/src/llm_extractor.py
./method_sectioned/src/parser.py
./method_sectioned/src/test_sectioned.py
./method_structured
./method_structured/__init__.py
./method_structured/src
./method_structured/src/__init__.py
./method_structured/src/llm.py
./method_structured/src/ocr.py
./method_structured/src/parser.py
./method_structured/src/schema.py
./method_trained_sectioned
./method_trained_sectioned/config
./method_trained_sectioned/config/boundary_visualization.txt
./method_trained_sectioned/config/raw_boundaries_analysis.json
./method_trained_sectioned/config/section_boundaries.json
./method_trained_sectioned/models
./method_trained_sectioned/src
./method_trained_sectioned/src/__init__.py
./method_trained_sectioned/src/layout_parser_trained.py
./method_trained_sectioned/src/llm_extractor.py
./method_trained_sectioned/src/parser.py
./method_trained_sectioned/src/test_parser.py
./method_trained_sectioned/src/train_section_detector.py
./README.md
./requirements.txt
./setup.sh
./test-ocr.py
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

Or use the helper script:

```bash
chmod +x setup.sh
./setup.sh run
```

Once running, simply upload your marksheet. The system will automatically:
1. Perform OCR and spatial analysis.
2. Trigger the **Structured** and **Dynamic** LLM pipelines in parallel.
3. Present a side-by-side comparison with instant export options.

---

## 🧪 Trained Section Detector (Optional)

The trained section detector learns **page-region boundaries** from labeled marksheets.
It does **not** save a deep-learning model file; it saves learned boundary rules as JSON.

**Training data location:**
- `data/training_data/`

**Outputs saved to:**
- `method_trained_sectioned/config/section_boundaries.json`
- `method_trained_sectioned/config/raw_boundaries_analysis.json`
- `method_trained_sectioned/config/boundary_visualization.txt`

**Run training:**
```bash
./setup.sh train
```

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
