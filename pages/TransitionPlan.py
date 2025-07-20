
import streamlit as st
import pandas as pd

st.set_page_config(page_title="📆 Transition Plan Tool", layout="wide")
st.title("📆 ESG Transition Plan (HVAC + CRREM)")

# Load datasets
try:
    archetypes = pd.read_excel("data/Building_Archetypes_CRREM_Compatible.xlsx")
    retrofit_costs = pd.read_excel("data/Retrofit_Costs_CRREM_Compatible.xlsx")
    esg_uplift = pd.read_excel("data/ESG_Valuation_Impacts_CRREM_Compatible.xlsx")
    crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
    emission_factors = pd.read_csv("data/crrem_emission_factors.csv")
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# Form Inputs
with st.form("transition_form"):
    st.subheader("🏢 Asset Details")
    col1, col2, col3 = st.columns(3)
    country = col1.selectbox("Country", sorted(archetypes["Country_code_CRREM"].dropna().unique()))
    asset_class = col2.selectbox("Asset Class", sorted(archetypes["Asset_Class"].dropna().unique()))
    vintage = col3.selectbox("Building Vintage", sorted(archetypes["Vintage"].dropna().unique()))

    match_typology = archetypes[
        (archetypes["Country_code_CRREM"] == country) &
        (archetypes["Asset_Class"] == asset_class) &
        (archetypes["Vintage"] == vintage)
    ]
    suggested_typology = match_typology.iloc[0]["Typology"] if not match_typology.empty else "N/A"
    st.markdown(f"💡 **Suggested Typology**: `{suggested_typology}`")

    current_typology = st.selectbox("Current Typology", archetypes["Typology"].dropna().unique(), index=0 if suggested_typology == "N/A" else archetypes["Typology"].tolist().index(suggested_typology))
    new_typology = st.selectbox("Target Typology", archetypes["Typology"].dropna().unique())

    col4, col5, col6 = st.columns(3)
    current_epc = col4.selectbox("Current EPC", ["G", "F", "E", "D", "C", "B", "A"])
    target_epc = col5.selectbox("Target EPC", ["G", "F", "E", "D", "C", "B", "A"], index=3)
    retrofit_year = col6.slider("Retrofit Year", 2024, 2035, 2025)

    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=5000)
    current_intensity = st.number_input("Current Carbon Intensity (kgCO₂/m²)", min_value=10.0, value=85.0)
    asset_value = st.number_input("Current Asset Value (€)", min_value=1_000_000, value=25_000_000)

    
    auto_epc = st.checkbox("🔍 Auto-infer Current EPC from intensity?", value=True)

    submitted = st.form_submit_button("📊 Generate Plan")


if submitted:
    try:
        
    # Auto-infer EPC if requested
    inferred_epc = None
    if auto_epc:
        try:
            epc_baselines = pd.read_excel("data/Energy_Performance_Baselines_CRREM_Compatible.xlsx")
            baseline_row = epc_baselines[
                (epc_baselines["country_code"] == country) &
                (epc_baselines["asset_class"] == asset_class)
            ].iloc[0]
            carbon_intensity = current_intensity
            for epc_band in ["A", "B", "C", "D", "E", "F", "G"]:
                if carbon_intensity <= baseline_row[f"{epc_band}_max"]:
                    inferred_epc = epc_band
                    break
            if inferred_epc:
                current_epc = inferred_epc
                st.info(f"📡 Auto-inferred Current EPC: **{inferred_epc}**")
            else:
                st.warning("⚠️ Could not infer EPC from carbon intensity.")
        except Exception as e:
            st.warning(f"Auto-inference failed: {e}")

    # EPC uplift lookup

        uplift_row = esg_uplift[
            (esg_uplift["Country"] == country) &
            (esg_uplift["From EPC"] == current_epc) &
            (esg_uplift["To EPC"] == target_epc)
        ].iloc[0]
        uplift_pct = uplift_row["Valuation Uplift (%)"]
        uplift_value = asset_value * uplift_pct / 100

        # Estimate savings
        carbon_saving = floor_area * 8  # 8 kgCO2/m² assumption
        post_intensity = current_intensity - (carbon_saving / floor_area)

        # CRREM check
        crrem_row = crrem_pathways[
            (crrem_pathways["region_code"] == country) &
            (crrem_pathways["asset_class"] == asset_class) &
            (crrem_pathways["year"] == retrofit_year)
        ]
        if crrem_row.empty:
            st.warning("No CRREM data available for this configuration.")
            target_intensity = None
            stranded = None
        else:
            target_intensity = crrem_row["target_carbon_intensity_kgco2m2"].values[0]
            stranded = post_intensity > target_intensity

        # Results
        st.subheader("📊 Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Valuation Uplift (€)", f"{uplift_value:,.0f}")
        col2.metric("Estimated CO₂ Savings", f"{carbon_saving:,.0f} kgCO₂")
        col3.metric("Post-Retrofit Intensity", f"{post_intensity:.1f} kgCO₂/m²")

        if target_intensity:
            st.markdown(f"CRREM Target: {target_intensity:.1f} kgCO₂/m²")
            if stranded:
                st.error("🚨 Asset remains stranded under CRREM.")
            else:
                st.success("✅ Compliant with CRREM target.")

        # Download summary
        summary = pd.DataFrame([{
            "Country": country,
            "Asset Class": asset_class,
            "Vintage": vintage,
            "Typology From": current_typology,
            "Typology To": new_typology,
            "Current EPC": current_epc,
            "Target EPC": target_epc,
            "Retrofit Year": retrofit_year,
            "Floor Area": floor_area,
            "Current Intensity": current_intensity,
            "Post Intensity": post_intensity,
            "CRREM Target": target_intensity,
            "Stranded": "Yes" if stranded else "No",
            "Asset Value (€)": asset_value,
            "Valuation Uplift (€)": uplift_value,
            "CO2 Saving (kg)": carbon_saving
        }])
        st.download_button("📥 Download Transition Plan CSV", summary.to_csv(index=False), file_name="transition_plan.csv")

    except Exception as e:
        st.error(f"Error: {e}")
