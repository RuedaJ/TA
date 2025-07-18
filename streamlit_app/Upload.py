
import streamlit as st
import pandas as pd
import tempfile
from backend.utils.file_validator import validate_csv

st.title("📂 Upload ESG Data")

st.markdown("Upload your ESG-related CSV files for validation and analysis.")

file_type = st.selectbox("Select file type to upload", ["assets", "utilities"])
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    result = validate_csv(tmp_path, file_type)

    if result["status"] == "success":
        st.success(result["message"])
        st.dataframe(result["data"].head(20))
    else:
        st.error(result["message"])
