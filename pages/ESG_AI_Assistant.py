
import streamlit as st
import pandas as pd
import tempfile
from backend.utils.file_validator import validate_csv

st.set_page_config(layout="wide")
st.title("🧠 ESG AI Assistant")

st.markdown("Upload your validated asset CSV and select an asset to receive a plain-language explanation of its ESG status.")

uploaded_file = st.file_uploader("Upload validated asset CSV", type=["csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    result = validate_csv(tmp_path, "assets")

    if result["status"] == "success":
        df = result["data"]

        asset_names = df["Asset Name"].unique()
        selected_asset = st.selectbox("Select an asset", asset_names)

        asset = df[df["Asset Name"] == selected_asset].iloc[0]

        st.subheader(f"📝 ESG Summary for {selected_asset}")

        carbon_intensity = asset["Carbon Intensity (kgCO2e/m²)"]
        energy_use = asset.get("Energy Consumption (kWh)", 0)
        floor_area = asset["Floor Area (m²)"]
        epc = asset.get("EPC Rating", "N/A")

        if carbon_intensity > 80:
            carbon_status = "🚨 Very high emissions. This asset is at high risk of becoming stranded under CRREM pathways."
        elif carbon_intensity > 60:
            carbon_status = "⚠️ Above-average carbon intensity. Retrofit action is likely needed before 2030."
        else:
            carbon_status = "✅ Carbon intensity is within or near target. No immediate action needed."

        if epc in ["F", "G"]:
            epc_status = "🚨 EPC rating is poor. Legal or market penalties may apply."
        elif epc in ["D", "E"]:
            epc_status = "⚠️ EPC is moderate. Consider upgrading for future-proofing."
        else:
            epc_status = "✅ EPC rating is acceptable or strong."

        energy_intensity = energy_use / floor_area if floor_area > 0 else 0
        energy_msg = f"Estimated energy use intensity is **{energy_intensity:.1f} kWh/m²**."

        st.markdown(f"""
        **Carbon Intensity:** {carbon_intensity:.1f} kgCO2e/m²  
        **EPC Rating:** {epc}  
        **Floor Area:** {floor_area} m²  
        **Total Energy Use:** {energy_use} kWh

        ---
        **AI Assistant Summary:**

        {carbon_status}  
        {epc_status}  
        {energy_msg}
        """)

    else:
        st.error(result["message"])
