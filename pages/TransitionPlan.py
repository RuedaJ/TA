
import streamlit as st
import pandas as pd

# Load data sources
hvac_map = pd.read_excel("data/Technical_Systems_CRREM_Compatible.xlsx")
esg_val = pd.read_excel("data/ESG_Valuation_Impacts_CRREM_Compatible.xlsx")
crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
asset_classes = pd.read_csv("data/crrem_asset_classes.csv")
archetypes = pd.read_excel("data/Building_Archetypes_CRREM_Compatible.xlsx")

st.set_page_config(page_title="📆 Transition Plan Tool", layout="wide")
st.title("📆 Transition Plan – Archetype + CRREM Alignment")

with st.form("transition_inputs"):
    st.subheader("🏢 Building Profile (Auto-suggest)")

    col1, col2, col3 = st.columns(3)
    country = col1.selectbox("Country", archetypes["Country_code_CRREM"].dropna().unique())
    asset_class = col2.selectbox("Asset Class", archetypes["Asset_Class"].dropna().unique())
    vintage = col3.selectbox("Building Vintage", archetypes["Vintage"].dropna().unique())

    # Filter and suggest current typology
    matching_archetypes = archetypes[
        (archetypes["Country_code_CRREM"] == country) &
        (archetypes["Asset_Class"] == asset_class) &
        (archetypes["Vintage"] == vintage)
    ]
    if not matching_archetypes.empty:
        suggested_typology = matching_archetypes.iloc[0]["Typology"]
    else:
        suggested_typology = "No match found"

    st.markdown(f"🛠️ **Suggested Current Typology**: `{suggested_typology}`")

    current_typology = st.selectbox("Confirm/Adjust Current HVAC Typology", hvac_map["Typology"].dropna().unique(), index=0 if suggested_typology == "No match found" else hvac_map["Typology"].dropna().tolist().index(suggested_typology) if suggested_typology in hvac_map["Typology"].values else 0)
    new_typology = st.selectbox("Target HVAC Typology", hvac_map["Typology"].dropna().unique(), index=1)

    col4, col5, col6 = st.columns(3)
    current_epc = col4.selectbox("Current EPC", ["G", "F", "E", "D", "C", "B", "A"])
    target_epc = col5.selectbox("Target EPC", ["G", "F", "E", "D", "C", "B", "A"], index=4)
    retrofit_year = col6.slider("Retrofit Year", 2024, 2035, 2025)

    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=5000)
    current_intensity = st.number_input("Current Carbon Intensity (kgCO₂/m²)", min_value=10.0, value=85.0)
    asset_value = st.number_input("Asset Value (€)", min_value=1000000, value=20000000)

    submitted = st.form_submit_button("Generate Transition Plan")

if submitted:
    try:
        # EPC uplift
        uplift_row = esg_val[
            (esg_val["Country"] == country) &
            (esg_val["From EPC"] == current_epc) &
            (esg_val["To EPC"] == target_epc)
        ].iloc[0]
        uplift_pct = uplift_row["Valuation Uplift (%)"]
        uplift_value = asset_value * (uplift_pct / 100)

        # Placeholder savings assumptions
        assumed_saving_per_m2 = 8.0  # kgCO2e/m2
        carbon_saving = assumed_saving_per_m2 * floor_area
        energy_saving = carbon_saving * 0.25

        post_intensity = current_intensity - (carbon_saving / floor_area)

        # CRREM pathway comparison
        pathway_row = crrem_pathways[
            (crrem_pathways["region_code"] == country) &
            (crrem_pathways["asset_class"] == asset_class) &
            (crrem_pathways["year"] == retrofit_year)
        ].iloc[0]
        target_intensity = pathway_row["target_carbon_intensity_kgco2m2"]
        stranded = post_intensity > target_intensity

        # Output
        st.subheader("📊 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Valuation Uplift (€)", f"{uplift_value:,.0f}")
        col2.metric("Carbon Saving (kgCO₂)", f"{carbon_saving:,.0f}")
        col3.metric("Post-Retrofit Intensity", f"{post_intensity:.1f} kgCO₂/m²")

        st.subheader("📌 CRREM Check")
        if stranded:
            st.error(f"🚨 Post-retrofit intensity exceeds CRREM target ({target_intensity:.1f})")
        else:
            st.success(f"✅ Compliant with CRREM target for {retrofit_year} ({target_intensity:.1f})")

        # Downloadable table
        result_df = pd.DataFrame([{
            "Country": country,
            "Asset Class": asset_class,
            "Vintage": vintage,
            "Current Typology": current_typology,
            "Target Typology": new_typology,
            "Current EPC": current_epc,
            "Target EPC": target_epc,
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
        st.error(f"Error generating plan: {e}")
