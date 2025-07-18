
import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
from backend.utils.file_validator import validate_csv

st.set_page_config(layout="wide")
st.title("📘 Stakeholder Playbooks – Investor View")

st.markdown("Upload your validated asset CSV file to generate ESG investment insights.")

uploaded_file = st.file_uploader("Upload validated asset CSV", type=["csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    result = validate_csv(tmp_path, "assets")

    if result["status"] == "success":
        df = result["data"]

        df["Energy Intensity (kWh/m²)"] = df.get("Energy Consumption (kWh)", 0) / df["Floor Area (m²)"]
        df["Stranding Year (est.)"] = df["Carbon Intensity (kgCO2e/m²)"].apply(
            lambda x: 2025 if x > 80 else (2030 if x > 60 else 2040)
        )
        df["Carbon Delta"] = df["Carbon Intensity (kgCO2e/m²)"] - 50  # Assume 50 is a CRREM-like target

        st.subheader("📈 Portfolio Highlights")
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg. Carbon Intensity", f"{df['Carbon Intensity (kgCO2e/m²)'].mean():.1f} kgCO2e/m²")
        col2.metric("Avg. Energy Intensity", f"{df['Energy Intensity (kWh/m²)'].mean():.1f} kWh/m²")
        col3.metric("Avg. Carbon Delta", f"{df['Carbon Delta'].mean():.1f}")

        st.subheader("🔥 Top 5 Stranded Assets by Carbon Delta")
        top5 = df.sort_values("Carbon Delta", ascending=False).head(5)
        st.dataframe(top5[["Asset Name", "Carbon Intensity (kgCO2e/m²)", "Carbon Delta", "Stranding Year (est.)"]])

        fig = px.bar(top5, x="Asset Name", y="Carbon Delta", color="Stranding Year (est.)",
                     title="Carbon Risk by Asset", text_auto=True)
        st.plotly_chart(fig)

        st.subheader("📉 Stranding Risk Summary")
        stranded_counts = df["Stranding Year (est.)"].value_counts().sort_index()
        fig2 = px.pie(values=stranded_counts.values, names=stranded_counts.index,
                      title="Portfolio Stranding Risk Distribution")
        st.plotly_chart(fig2)

        st.download_button("Download Portfolio Summary CSV", df.to_csv(index=False), file_name="portfolio_summary.csv")

    else:
        st.error(result["message"])
