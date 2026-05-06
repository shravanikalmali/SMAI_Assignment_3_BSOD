import streamlit as st
import os
import tempfile
import json
import pandas as pd
from method_structured.src.parser import parse_document as parse_structured
from method_dynamic.src.parser import parse_dynamic
from method_sectioned.src.parser import parse_sectioned

st.set_page_config(page_title="Comparative Marksheet Parser", layout="wide")

st.title("📊 Comparative Marksheet Analysis")
st.write("Upload a document to run multiple extraction methods simultaneously.")

def flatten_json(y):
    """Utility to flatten dynamic JSON for CSV export"""
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x
    flatten(y)
    return out

def get_structured_csv(data):
    """Converts structured marksheet data to a clean CSV format"""
    # 1. Subject Table
    subjects_df = pd.DataFrame(data.get("subjects", []))
    
    # 2. Add student metadata as columns to every row (for a flat record)
    meta_cols = ["student_name", "mother_name", "father_name", "dob", "school_name", "board", "exam_name", "year", "result_status"]
    for col in meta_cols:
        subjects_df[col] = data.get(col, "N/A")
    
    return subjects_df.to_csv(index=False)

def get_sectioned_csv(data):
    """Converts sectioned marksheet data to CSV format"""
    # Extract subjects
    subjects_df = pd.DataFrame(data.get("subjects", []))
    
    # Add metadata to each row
    meta_cols = ["student_name", "father_name", "mother_name", "roll_number", 
                 "total_marks", "maximum_marks", "percentage", "result", "division"]
    for col in meta_cols:
        subjects_df[col] = data.get(col, "N/A")
    
    return subjects_df.to_csv(index=False)

uploaded_file = st.file_uploader("Choose a marksheet", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    st.markdown("---")
    
    # Execution Phase - 3 columns for 3 methods
    results = {}
    
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        with st.status("🏗 Structured Method...", expanded=True) as status:
            try:
                results["Structured"] = parse_structured(tmp_path)
                status.update(label="Structured Extraction Complete!", state="complete")
            except Exception as e:
                results["Structured"] = {"error": str(e)}
                status.update(label="Structured Extraction Failed!", state="error")
            
    with col_status2:
        with st.status("🧪 Dynamic Method...", expanded=True) as status:
            try:
                results["Dynamic"] = parse_dynamic(tmp_path)
                status.update(label="Dynamic Extraction Complete!", state="complete")
            except Exception as e:
                results["Dynamic"] = {"error": str(e)}
                status.update(label="Dynamic Extraction Failed!", state="error")

    with col_status3:
        with st.status("📍 Section-Based (PaddleOCR Layout)...", expanded=True) as status:
            try:
                results["Sectioned"] = parse_sectioned(tmp_path, debug=False)
                status.update(label="Section-Based Extraction Complete!", state="complete")
            except Exception as e:
                results["Sectioned"] = {"error": str(e)}
                status.update(label="Section-Based Extraction Failed!", state="error")

    # Display Phase - 3 tabs for 3 methods
    tab1, tab2, tab3 = st.tabs(["🏗 Structured Output", "🧪 Dynamic Output", "📍 Section-Based Output (PaddleOCR)"])

    # Tab 1: Structured Output
    with tab1:
        data = results["Structured"]
        if "error" in data:
            st.error(f"Error: {data['error']}")
            if "raw" in data:
                with st.expander("View Raw Output"):
                    st.code(data["raw"])
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.json(data)
            with c2:
                st.subheader("💾 Export Options")
                
                # JSON
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "structured_ext.json", "application/json", key="structured_json")
                
                # CSV
                try:
                    csv_data = get_structured_csv(data)
                    st.download_button("Download Tabular CSV", csv_data, "structured_ext.csv", "text/csv", key="structured_csv")
                except Exception as e:
                    st.warning(f"CSV Export not possible: {str(e)}")

    # Tab 2: Dynamic Output
    with tab2:
        data = results["Dynamic"]
        if "error" in data:
            st.error(f"Error: {data['error']}")
            if "raw" in data:
                with st.expander("View Raw Output"):
                    st.code(data["raw"])
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.json(data)
            with c2:
                st.subheader("💾 Export Options")
                
                # JSON
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "dynamic_ext.json", "application/json", key="dynamic_json")
                
                # CSV (Flattened)
                try:
                    flattened = flatten_json(data)
                    df_flat = pd.DataFrame([flattened])
                    csv_flat = df_flat.to_csv(index=False)
                    st.download_button("Download Flattened CSV", csv_flat, "dynamic_ext.csv", "text/csv", key="dynamic_csv")
                except Exception as e:
                    st.warning(f"CSV Export not possible for this dynamic structure: {str(e)}")

    # Tab 3: Section-Based Output (YOURS)
    with tab3:
        data = results["Sectioned"]
        if "error" in data:
            st.error(f"Error: {data['error']}")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                # Display the extracted data
                st.json(data)
                
                # Show metadata if available
                if "_metadata" in data:
                    with st.expander("📊 Parser Metadata (How it worked)"):
                        st.json(data["_metadata"])
                        
                        # Show explanation of what happened
                        st.markdown("**🔍 What this parser did:**")
                        metadata = data["_metadata"]
                        
                        if metadata.get("parser_type") == "sectioned_paddleocr":
                            st.markdown("""
                            - ✅ Used **PaddleOCR with layout detection** to identify document sections
                            - ✅ Automatically detected sections like: Student Info, Subject Table, Totals
                            - ✅ Sent each section to a **specialized LLM prompt**
                            """)
                            
                            sections_found = metadata.get("sections_found", {})
                            if sections_found:
                                st.markdown("**Sections detected:**")
                                for section, length in sections_found.items():
                                    st.markdown(f"  - `{section}`: {length} characters")
                            
                            if metadata.get("fallback_used"):
                                st.warning("⚠️ Fallback was used - section extraction had issues")
                            else:
                                st.success("✅ Section extraction worked without fallback")
                            
            with c2:
                st.subheader("💾 Export Options")
                
                # JSON
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "sectioned_ext.json", "application/json", key="sectioned_json")
                
                # CSV (Subject table format)
                try:
                    csv_data = get_sectioned_csv(data)
                    if csv_data and len(csv_data) > 10:
                        st.download_button("Download Subjects CSV", csv_data, "sectioned_subjects.csv", "text/csv", key="sectioned_csv")
                except Exception as e:
                    st.info(f"CSV Export: {str(e)}")
                
                # Summary Card
                st.markdown("---")
                st.subheader("📋 Extraction Summary")
                
                # Create a nice summary
                summary_data = {
                    "Student Name": data.get("student_name", "❌ Not found"),
                    "Roll Number": data.get("roll_number", "❌ Not found"),
                    "Father's Name": data.get("father_name", "❌ Not found"),
                    "Subjects Found": len(data.get("subjects", [])),
                    "Total Marks": data.get("total_marks", "❌ Not found"),
                    "Percentage": data.get("percentage", "❌ Not found"),
                    "Result": data.get("result", "❌ Not found")
                }
                
                for key, value in summary_data.items():
                    if value and value != "❌ Not found":
                        st.metric(key, value)
                    else:
                        st.markdown(f"**{key}:** {value}")
                
                # Show first few subjects
                subjects = data.get("subjects", [])
                if subjects:
                    st.markdown("---")
                    st.markdown("**📚 First few subjects:**")
                    for subj in subjects[:3]:
                        marks = subj.get("marks", "?")
                        st.markdown(f"- {subj.get('subject', 'Unknown')}: {marks} marks")
                    if len(subjects) > 3:
                        st.markdown(f"... and {len(subjects) - 3} more")

    # Clean up temp file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

# Add sidebar with information about the methods
with st.sidebar:
    st.markdown("## 📖 About the Methods")
    
    st.markdown("### 🏗 Structured Method")
    st.caption("Fixed schema extraction with one LLM call")
    
    st.markdown("### 🧪 Dynamic Method")
    st.caption("Open-world extraction, flexible schema")
    
    st.markdown("### 📍 Section-Based Method (NEW)")
    st.caption("""
    **Uses PaddleOCR Layout Detection:**
    1. Detects document sections (tables, headers, etc.)
    2. Extracts each section separately
    3. Sends focused prompts to LLM
    4. Merges results
    
    **Advantages:**
    - Less hallucination
    - Better accuracy for tables
    - Understands document structure
    """)
    
    st.markdown("---")
    st.markdown("### 🔧 Requirements")
    st.code("""
    pip install paddlepaddle
    pip install paddleocr
    pip install groq
    pip install python-dotenv
    """)