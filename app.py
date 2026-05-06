import streamlit as st
import os
import tempfile
import json
import pandas as pd
from method_structured.src.parser import parse_document as parse_structured
from method_dynamic.src.parser import parse_dynamic
from method_sectioned.src.parser import parse_sectioned
from method_trained_sectioned.src.parser import parse_sectioned_trained  # Add trained method

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
    subjects_df = pd.DataFrame(data.get("subjects", []))
    meta_cols = ["student_name", "mother_name", "father_name", "dob", "school_name", "board", "exam_name", "year", "result_status"]
    for col in meta_cols:
        subjects_df[col] = data.get(col, "N/A")
    return subjects_df.to_csv(index=False)

def get_sectioned_csv(data):
    """Converts sectioned marksheet data to CSV format"""
    subjects_df = pd.DataFrame(data.get("subjects", []))
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
    
    # Execution Phase - 4 columns for 4 methods
    results = {}
    
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    
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
        with st.status("📍 Section-Based (Rule)...", expanded=True) as status:
            try:
                results["Sectioned"] = parse_sectioned(tmp_path, debug=False)
                status.update(label="Section-Based Extraction Complete!", state="complete")
            except Exception as e:
                results["Sectioned"] = {"error": str(e)}
                status.update(label="Section-Based Extraction Failed!", state="error")

    with col_status4:
        with st.status("🎯 Section-Based (Trained ML)...", expanded=True) as status:
            try:
                results["Trained ML"] = parse_sectioned_trained(tmp_path, debug=False)
                status.update(label="Trained ML Extraction Complete!", state="complete")
            except Exception as e:
                results["Trained ML"] = {"error": str(e)}
                status.update(label="Trained ML Extraction Failed!", state="error")

    # Display Phase - 4 tabs for 4 methods
    tab1, tab2, tab3, tab4 = st.tabs(["🏗 Structured Output", "🧪 Dynamic Output", "📍 Section-Based (Rule)", "🎯 Section-Based (Trained ML)"])

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
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "structured_ext.json", "application/json", key="structured_json")
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
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "dynamic_ext.json", "application/json", key="dynamic_json")
                try:
                    flattened = flatten_json(data)
                    df_flat = pd.DataFrame([flattened])
                    csv_flat = df_flat.to_csv(index=False)
                    st.download_button("Download Flattened CSV", csv_flat, "dynamic_ext.csv", "text/csv", key="dynamic_csv")
                except Exception as e:
                    st.warning(f"CSV Export not possible for this dynamic structure: {str(e)}")

    # Tab 3: Section-Based Output (Rule-based)
    with tab3:
        data = results["Sectioned"]
        if "error" in data:
            st.error(f"Error: {data['error']}")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.json(data)
                if "_metadata" in data:
                    with st.expander("📊 Parser Metadata"):
                        st.json(data["_metadata"])
                        st.markdown("**🔍 Rule-based section detection:**")
                        st.markdown("""
                        - Uses **fixed position thresholds** (0-25%, 25-65%, 65-100%)
                        - Does NOT learn from data
                        - Same rules for all marksheets
                        """)
            with c2:
                st.subheader("💾 Export Options")
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "sectioned_ext.json", "application/json", key="sectioned_json")
                try:
                    csv_data = get_sectioned_csv(data)
                    if csv_data and len(csv_data) > 10:
                        st.download_button("Download Subjects CSV", csv_data, "sectioned_subjects.csv", "text/csv", key="sectioned_csv")
                except Exception as e:
                    st.info(f"CSV Export: {str(e)}")
                
                st.markdown("---")
                st.subheader("📋 Extraction Summary")
                summary_data = {
                    "Student Name": data.get("student_name", "❌ Not found"),
                    "Roll Number": data.get("roll_number", "❌ Not found"),
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

    # Tab 4: Trained ML Output
    with tab4:
        data = results["Trained ML"]
        if "error" in data:
            st.error(f"Error: {data['error']}")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.json(data)
                if "_metadata" in data:
                    with st.expander("📊 ML Model Metadata"):
                        st.json(data["_metadata"])
                        st.markdown("**🔍 What the trained ML model does:**")
                        st.markdown("""
                        - ✅ Uses **ML-trained section detection** from 24 marksheets
                        - ✅ Learned optimal section boundaries from your data
                        - ✅ Adapts to your specific marksheet format
                        - ✅ Pre-trained - loads instantly, no re-training
                        """)
                        
                        boundaries = data["_metadata"].get("boundaries_used", {})
                        if boundaries:
                            st.markdown("**📐 Learned section boundaries:**")
                            for section, bounds in boundaries.items():
                                st.markdown(f"  - `{section}`: {bounds['y_min']:.1f}% - {bounds['y_max']:.1f}% of page")
            with c2:
                st.subheader("💾 Export Options")
                json_data = json.dumps(data, indent=2)
                st.download_button("Download JSON", json_data, "trained_ml_ext.json", "application/json", key="trained_json")
                
                # CSV Export
                try:
                    if "subjects" in data and data["subjects"]:
                        subjects_df = pd.DataFrame(data["subjects"])
                        meta_fields = ["student_name", "father_name", "mother_name", "roll_number", 
                                      "total_marks", "maximum_marks", "percentage", "result"]
                        for field in meta_fields:
                            if field in data:
                                subjects_df[field] = data[field]
                        csv_data = subjects_df.to_csv(index=False)
                        st.download_button("Download Subjects CSV", csv_data, "trained_ml_subjects.csv", "text/csv", key="trained_csv")
                except Exception as e:
                    st.info(f"CSV Export: {str(e)}")
                
                st.markdown("---")
                st.subheader("📋 Extraction Summary")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Student Name", data.get("student_name", "❌")[:20] if data.get("student_name") else "❌")
                    st.metric("Roll Number", data.get("roll_number", "❌"))
                    st.metric("Subjects", len(data.get("subjects", [])))
                with col2:
                    st.metric("Total Marks", data.get("total_marks", "❌"))
                    st.metric("Percentage", data.get("percentage", "❌"))
                    st.metric("Result", data.get("result", "❌"))
                
                subjects = data.get("subjects", [])
                if subjects:
                    st.markdown("---")
                    st.markdown("**📚 First few subjects:**")
                    for subj in subjects[:3]:
                        marks = subj.get("marks", "?")
                        grade = subj.get("grade", "")
                        grade_str = f" (Grade: {grade})" if grade else ""
                        st.markdown(f"- {subj.get('subject', 'Unknown')}: {marks} marks{grade_str}")

    # Clean up temp file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

# Sidebar
with st.sidebar:
    st.markdown("## 📖 About the Methods")
    
    st.markdown("### 🏗 Structured Method")
    st.caption("Fixed schema extraction with one LLM call")
    
    st.markdown("### 🧪 Dynamic Method")
    st.caption("Open-world extraction, flexible schema")
    
    st.markdown("### 📍 Section-Based (Rule)")
    st.caption("Fixed position thresholds (0-25%, 25-65%, 65-100%)")
    
    st.markdown("### 🎯 Section-Based (Trained ML)")
    st.caption("""
    **Learns from 24 training marksheets:**
    - Analyzes text positions across training data
    - Automatically finds optimal section boundaries
    - Pre-trained model loads instantly
    - No re-training when app runs
    
    **Training was done once offline** on 24 marksheets
    """)
    
    # Show if trained model is available
    if os.path.exists("method_trained_sectioned/config/section_boundaries.json"):
        st.success("✅ Trained ML model is ready!")
        with open("method_trained_sectioned/config/section_boundaries.json", "r") as f:
            boundaries = json.load(f)
        st.markdown("**Learned boundaries:**")
        for section, bounds in boundaries.items():
            st.caption(f"• {section}: {bounds['y_min']:.0f}-{bounds['y_max']:.0f}%")
    else:
        st.warning("⚠️ Train ML model first:")
        st.code("cd method_trained_sectioned && python3 train_fixed.py")
    
    st.markdown("---")
    st.markdown("### 🔧 Requirements")
    st.code("""
    pip install streamlit
    pip install easyocr
    pip install groq
    pip install python-dotenv
    pip install pandas
    pip install opencv-python
    """)