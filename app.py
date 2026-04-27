import streamlit as st
import os
import tempfile
import json
import pandas as pd
from method_structured.src.parser import parse_document as parse_structured
from method_dynamic.src.parser import parse_dynamic

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

uploaded_file = st.file_uploader("Choose a marksheet", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    st.markdown("---")
    
    # Execution Phase
    results = {}
    
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        with st.status("Running Structured Method...", expanded=True) as status:
            results["Structured"] = parse_structured(tmp_path)
            status.update(label="Structured Extraction Complete!", state="complete")
            
    with col_status2:
        with st.status("Running Dynamic Method...", expanded=True) as status:
            results["Dynamic"] = parse_dynamic(tmp_path)
            status.update(label="Dynamic Extraction Complete!", state="complete")

    # Display Phase
    tab1, tab2 = st.tabs(["🏗 Structured Output", "🧪 Dynamic Output"])

    with tab1:
        data = results["Structured"]
        if "error" in data:
            st.error(data["error"])
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.json(data)
            with c2:
                st.subheader("💾 Export Options")
                
                # JSON
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "structured_ext.json", "application/json")
                
                # CSV
                try:
                    csv_data = get_structured_csv(data)
                    st.download_button("Download Tabular CSV", csv_data, "structured_ext.csv", "text/csv")
                except Exception as e:
                    st.warning(f"CSV Export not possible: {str(e)}")

    with tab2:
        data = results["Dynamic"]
        if "error" in data:
            st.error(data["error"])
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.json(data)
            with c2:
                st.subheader("💾 Export Options")
                
                # JSON
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "dynamic_ext.json", "application/json")
                
                # CSV (Flattened)
                try:
                    flattened = flatten_json(data)
                    df_flat = pd.DataFrame([flattened])
                    csv_flat = df_flat.to_csv(index=False)
                    st.download_button("Download Flattened CSV", csv_flat, "dynamic_ext.csv", "text/csv")
                except Exception as e:
                    st.warning(f"CSV Export not possible for this dynamic structure: {str(e)}")

    if os.path.exists(tmp_path):
        os.remove(tmp_path)
