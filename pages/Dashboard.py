
import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
from backend.utils.file_validator import validate_csv

st.title("📊 Portfolio ESG Dashboard")

st.markdown("Upload your validated asset CSV file to view KPIs like carbon intensity, energy use, and stranding year.")

uploaded_file = st.file_uploader("Upload validated asset CSV", type=["csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    result = validate_csv(tmp_path, "assets")

    if result["status"] == "success":
        df = result["data"]

        # Compute additional KPIs if needed
        df["Energy Intensity (kWh/m²)"] = df.get("Energy Consumption (kWh)", 0) / df["Floor Area (m²)"]
        df["Stranding Year (est.)"] = df["Carbon Intensity (kgCO2e/m²)"].apply(
            lambda x: 2025 if x > 80 else (2030 if x > 60 else 2040)
        )

        st.success("Data loaded successfully.")
        st.dataframe(df.head(20))

        kpi1 = df["Carbon Intensity (kgCO2e/m²)"].mean()
        kpi2 = df["Energy Intensity (kWh/m²)"].mean()
        kpi3 = df["Stranding Year (est.)"].value_counts().idxmax()

        col1, col2, col3 = st.columns(3)
        col1.metric("Avg. Carbon Intensity", f"{kpi1:.1f} kgCO2e/m²")
        col2.metric("Avg. Energy Intensity", f"{kpi2:.1f} kWh/m²")
        col3.metric("Most Common Stranding Year", f"{kpi3}")

        fig = px.histogram(df, x="Stranding Year (est.)", title="Stranding Year Distribution")
        st.plotly_chart(fig)

    else:
        st.error(result["message"])
