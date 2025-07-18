
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from backend.utils.file_validator import validate_csv

st.set_page_config(layout="wide")
st.title("📉 CRREM Stranding Plot Per Asset")

uploaded_file = st.file_uploader("Upload validated asset CSV", type=["csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    result = validate_csv(tmp_path, "assets")

    if result["status"] == "success":
        df = result["data"]

        asset_names = df["Asset Name"].unique()
        selected_asset = st.selectbox("Select an asset to plot", asset_names)

        asset_df = df[df["Asset Name"] == selected_asset].iloc[0]

        # Placeholder: CRREM pathway for this asset type
        crrem_years = list(range(2020, 2051))
        crrem_threshold = [100 - (i - 2020) * 1.2 for i in crrem_years]  # Sample decreasing line

        fig, ax = plt.subplots()
        ax.plot(crrem_years, crrem_threshold, label="CRREM Target Pathway", color="green")
        ax.hlines(asset_df["Carbon Intensity (kgCO2e/m²)"], 2020, 2050, colors="red", linestyles="--", label="Current Intensity")

        ax.set_title(f"Stranding Year Estimation for {selected_asset}")
        ax.set_xlabel("Year")
        ax.set_ylabel("kgCO2e/m²")
        ax.legend()
        ax.grid(True)

        # Estimate stranding year
        stranding_year = next((year for year, target in zip(crrem_years, crrem_threshold)
                               if asset_df["Carbon Intensity (kgCO2e/m²)"] > target), "2050+")
        st.metric("Estimated Stranding Year", stranding_year)

        st.pyplot(fig)

    else:
        st.error(result["message"])
