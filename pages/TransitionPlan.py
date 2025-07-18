
import streamlit as st
import pandas as pd

# Load datasets
hvac_map = pd.read_excel("data/Technical_Systems_CRREM_Compatible.xlsx")
esg_val = pd.read_excel("data/ESG_Valuation_Impacts_CRREM_Compatible.xlsx")
crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
emission_factors = pd.read_excel("data/Utility_Tariffs_CRREM_Compatible.xlsx")
asset_classes = pd.read_csv("data/crrem_asset_classes.csv")

st.set_page_config(page_title="📆 ESG Transition Plan (HVAC + CRREM)", layout="wide")
st.title("📆 ESG Transition Planner")

with st.form("transition_inputs"):
    col1, col2, col3 = st.columns(3)
    asset_class = col1.selectbox("Asset Class (CRREM)", asset_classes["asset_class"].dropna().unique())
    country = col2.selectbox("Country", crrem_pathways["region_code"].dropna().unique())
    current_system = col3.selectbox("Current HVAC System", hvac_map["Current System"].dropna().unique())
    new_system = st.selectbox("New HVAC System", hvac_map["New System"].dropna().unique())

    current_epc = st.selectbox("Current EPC", ["G", "F", "E", "D", "C", "B", "A"])
    new_epc = st.selectbox("Target EPC", ["G", "F", "E", "D", "C", "B", "A"], index=5)
    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=5000)
    current_intensity = st.number_input("Current Carbon Intensity (kgCO₂/m²)", min_value=10.0, value=85.0)
    asset_value = st.number_input("Current Asset Value (€)", min_value=1000000, value=25000000)
    retrofit_year = st.slider("Retrofit Year", 2024, 2035, value=2025)

    submitted = st.form_submit_button("Generate Plan")

if submitted:
    try:
        # Lookup HVAC retrofit impacts
        hvac_row = hvac_map.query("`Current System` == @current_system and `New System` == @new_system").iloc[0]
        capex = hvac_row["CapEx (€)"]
        carbon_saving = hvac_row["Annual Carbon Saving (kgCO2e)"]
        energy_saving = hvac_row["Annual Energy Saving (kWh)"]

        # Lookup EPC uplift
        uplift_row = esg_val.query("Country == @country and `From EPC` == @current_epc and `To EPC` == @new_epc").iloc[0]
        uplift_pct = uplift_row["Valuation Uplift (%)"]
        uplift_value = asset_value * (uplift_pct / 100)

        # Calculate post-retrofit carbon intensity
        post_intensity = current_intensity - (carbon_saving / floor_area)

        # CRREM pathway check
        pathway_row = crrem_pathways.query("region_code == @country and asset_class == @asset_class and year == @retrofit_year").iloc[0]
        target_intensity = pathway_row["target_carbon_intensity_kgco2m2"]
        stranded = post_intensity > target_intensity

        # Display outputs
        st.subheader("📊 Transition Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("CapEx (€)", f"{capex:,.0f}")
        col2.metric("Valuation Uplift (€)", f"{uplift_value:,.0f} ({uplift_pct:.1f}%)")
        col3.metric("Post-Retrofit Intensity", f"{post_intensity:.1f} kgCO₂/m²")

        st.subheader("📉 Emissions & CRREM Check")
        st.markdown(f"**Estimated Annual Carbon Saving**: {carbon_saving:,.0f} kgCO₂")
        st.markdown(f"**Estimated Annual Energy Saving**: {energy_saving:,.0f} kWh")

        if stranded:
            st.error(f"🚨 This asset remains stranded after retrofit. CRREM target for {retrofit_year}: {target_intensity:.1f} kgCO₂/m².")
        else:
            st.success(f"✅ This asset meets CRREM target for {retrofit_year} ({target_intensity:.1f} kgCO₂/m²).")

        result_df = pd.DataFrame([{
            "Asset Class": asset_class,
            "Country": country,
            "Current HVAC": current_system,
            "New HVAC": new_system,
            "Current EPC": current_epc,
            "Target EPC": new_epc,
            "Floor Area (m²)": floor_area,
            "Current Intensity": current_intensity,
            "Post Intensity": post_intensity,
            "CRREM Target": target_intensity,
            "Stranded?": "Yes" if stranded else "No",
            "Asset Value (€)": asset_value,
            "Valuation Uplift (€)": uplift_value,
            "CapEx (€)": capex,
            "Carbon Saving (kgCO2e)": carbon_saving,
            "Energy Saving (kWh)": energy_saving,
            "Retrofit Year": retrofit_year
        }])

        st.download_button("📥 Download Transition Summary", result_df.to_csv(index=False), file_name="transition_plan_crrem.csv")

    except Exception as e:
        st.error(f"Error in plan generation: {e}")
