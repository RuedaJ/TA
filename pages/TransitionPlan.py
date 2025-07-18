
import streamlit as st
import pandas as pd

# Load required data files
hvac_map = pd.read_excel("data/Technical_Systems_CRREM_Compatible.xlsx")
esg_val = pd.read_excel("data/ESG_Valuation_Impacts_CRREM_Compatible.xlsx")
crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
asset_classes = pd.read_csv("data/crrem_asset_classes.csv")

st.set_page_config(page_title="📆 Transition Plan Tool", layout="wide")
st.title("📆 Transition Plan – HVAC, EPC & CRREM")

with st.form("transition_inputs"):
    col1, col2, col3 = st.columns(3)
    asset_class = col1.selectbox("Asset Class (CRREM)", asset_classes["asset_class"].dropna().unique())
    country = col2.selectbox("Country", crrem_pathways["region_code"].dropna().unique())
    current_typology = col3.selectbox("Current HVAC Typology", hvac_map["Typology"].dropna().unique())
    new_typology = st.selectbox("Target HVAC Typology", hvac_map["Typology"].dropna().unique())

    col4, col5, col6 = st.columns(3)
    current_epc = col4.selectbox("Current EPC Rating", ["G", "F", "E", "D", "C", "B", "A"])
    new_epc = col5.selectbox("Target EPC Rating", ["G", "F", "E", "D", "C", "B", "A"], index=5)
    retrofit_year = col6.slider("Retrofit Year", 2024, 2035, 2025)

    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=5000)
    current_intensity = st.number_input("Current Carbon Intensity (kgCO₂/m²)", min_value=10.0, value=85.0)
    asset_value = st.number_input("Current Asset Value (€)", min_value=1000000, value=25000000)

    submitted = st.form_submit_button("Generate Transition Plan")

if submitted:
    try:
        # Estimate carbon savings arbitrarily (due to lack of system-specific deltas)
        assumed_saving_per_m2 = 8.0  # placeholder value (kgCO₂/m²/year)
        carbon_saving = assumed_saving_per_m2 * floor_area
        energy_saving = carbon_saving * 0.25  # assume 0.25 kgCO₂ per kWh for now

        # EPC uplift
        uplift_row = esg_val[(esg_val["Country"] == country) & (esg_val["From EPC"] == current_epc) & (esg_val["To EPC"] == new_epc)].iloc[0]
        uplift_pct = uplift_row["Valuation Uplift (%)"]
        uplift_value = asset_value * (uplift_pct / 100)

        # Estimate post-retrofit intensity
        post_intensity = current_intensity - (carbon_saving / floor_area)

        # Compare with CRREM
        pathway_row = crrem_pathways.query("asset_class == @asset_class and region_code == @country and year == @retrofit_year").iloc[0]
        target_intensity = pathway_row["target_carbon_intensity_kgco2m2"]
        stranded = post_intensity > target_intensity

        # Output
        st.subheader("📊 Retrofit & Financial Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Valuation Uplift (€)", f"{uplift_value:,.0f} ({uplift_pct:.1f}%)")
        col2.metric("Carbon Saving (kgCO₂)", f"{carbon_saving:,.0f}")
        col3.metric("Post Intensity", f"{post_intensity:.1f} kgCO₂/m²")

        st.subheader("📌 CRREM Check")
        if stranded:
            st.error(f"🚨 Still stranded after retrofit. CRREM target for {retrofit_year}: {target_intensity:.1f}")
        else:
            st.success(f"✅ Retrofit achieves CRREM compliance. Target: {target_intensity:.1f} kgCO₂/m²")

        result_df = pd.DataFrame([{
            "Asset Class": asset_class,
            "Country": country,
            "Current HVAC": current_typology,
            "New HVAC": new_typology,
            "Current EPC": current_epc,
            "Target EPC": new_epc,
            "Retrofit Year": retrofit_year,
            "Floor Area (m²)": floor_area,
            "Current Intensity": current_intensity,
            "Post Intensity": post_intensity,
            "CRREM Target": target_intensity,
            "Stranded?": "Yes" if stranded else "No",
            "Asset Value (€)": asset_value,
            "Valuation Uplift (€)": uplift_value,
            "Carbon Saving (kgCO₂)": carbon_saving,
            "Energy Saving (kWh)": energy_saving
        }])

        st.download_button("📥 Download Transition Plan", result_df.to_csv(index=False), file_name="transition_summary.csv")

    except Exception as e:
        st.error(f"Error during processing: {e}")
