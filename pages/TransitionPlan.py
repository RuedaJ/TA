
import streamlit as st
import pandas as pd

st.set_page_config(page_title="📆 Transition Plan Tool", layout="wide")
st.title("📆 ESG Transition Plan (with EPC Inference)")

# Load datasets
try:
    archetypes = pd.read_excel("data/Building_Archetypes_CRREM_Compatible.xlsx")
    retrofit_costs = pd.read_excel("data/Retrofit_Costs_CRREM_Compatible.xlsx")
    esg_uplift = pd.read_excel("data/ESG_Valuation_Impacts_CRREM_TEMPLATE.xlsx")
    crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
    epc_baselines = pd.read_excel("data/Energy_Performance_Baselines_CRREM_ALL_COUNTRIES.xlsx")
except Exception as e:
    st.error(f"❌ Data load error: {e}")
    st.stop()

with st.form("transition_form"):
    st.subheader("🏢 Asset Definition")

    col1, col2, col3 = st.columns(3)
    country = col1.selectbox("Country", sorted(archetypes["Country_code_CRREM"].dropna().unique()))
    asset_class = col2.selectbox("Asset Class", sorted(archetypes["Asset_Class"].dropna().unique()))
    vintage = col3.selectbox("Vintage", sorted(archetypes["Vintage"].dropna().unique()))

    matching = archetypes[
        (archetypes["Country_code_CRREM"] == country) &
        (archetypes["Asset_Class"] == asset_class) &
        (archetypes["Vintage"] == vintage)
    ]
    suggested_typology = matching.iloc[0]["Typology"] if not matching.empty else "N/A"
    st.markdown(f"💡 Suggested Typology: `{suggested_typology}`")

    col4, col5 = st.columns(2)
    current_typology = col4.selectbox("Current Typology", archetypes["Typology"].dropna().unique())
    new_typology = col5.selectbox("Target Typology", archetypes["Typology"].dropna().unique())

    st.subheader("📉 Performance & Retrofit Details")
    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=5000)
    current_intensity = st.number_input("Current Carbon Intensity (kgCO₂/m²)", value=85.0)
    asset_value = st.number_input("Current Asset Value (€)", min_value=1_000_000, value=25_000_000)

    col6, col7 = st.columns(2)
    target_epc = col6.selectbox("Target EPC", ["G", "F", "E", "D", "C", "B", "A"], index=3)
    retrofit_year = col7.slider("Retrofit Year", 2024, 2035, value=2025)

    auto_epc = st.checkbox("🔍 Auto-infer current EPC from carbon intensity?", value=True)
    manual_epc = st.selectbox("Or select manually", ["G", "F", "E", "D", "C", "B", "A"], index=4)

    submitted = st.form_submit_button("📊 Generate Plan")

if submitted:
    try:
        # Auto-infer EPC from intensity if selected
        if auto_epc:
            try:
                baseline_row = epc_baselines[
                    (epc_baselines["country_code"] == country) &
                    (epc_baselines["asset_class"] == asset_class)
                ].iloc[0]
                current_epc = None
                for epc_band in ["A", "B", "C", "D", "E", "F", "G"]:
                    if current_intensity <= baseline_row[f"{epc_band}_max"]:
                        current_epc = epc_band
                        break
                if current_epc:
                    st.info(f"📡 Auto-inferred Current EPC: **{current_epc}**")
                else:
                    st.warning("Could not infer EPC from intensity.")
                    current_epc = manual_epc
            except Exception as e:
                st.warning(f"⚠️ Inference failed: {e}")
                current_epc = manual_epc
        else:
            current_epc = manual_epc

        # Compute uplift
        uplift_row = esg_uplift[
            (esg_uplift["Country"] == country) &
            (esg_uplift["From EPC"] == current_epc) &
            (esg_uplift["To EPC"] == target_epc)
        ].iloc[0]
        uplift_pct = uplift_row["Valuation Uplift (%)"]
        uplift_value = asset_value * uplift_pct / 100

        # Estimate savings
        carbon_saving = floor_area * 8  # kgCO2/m² assumption
        post_intensity = current_intensity - (carbon_saving / floor_area)

        # CRREM compliance
        crrem_row = crrem_pathways[
            (crrem_pathways["region_code"] == country) &
            (crrem_pathways["asset_class"] == asset_class) &
            (crrem_pathways["year"] == retrofit_year)
        ]
        if crrem_row.empty:
            target_intensity = None
            stranded = None
        else:
            target_intensity = crrem_row["target_carbon_intensity_kgco2m2"].values[0]
            stranded = post_intensity > target_intensity

        # Display results
        st.subheader("📊 Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Valuation Uplift (€)", f"{uplift_value:,.0f}")
        col2.metric("Carbon Savings", f"{carbon_saving:,.0f} kgCO₂")
        col3.metric("Post-Retrofit Intensity", f"{post_intensity:.1f} kgCO₂/m²")

        if target_intensity:
            st.markdown(f"🎯 CRREM Target: {target_intensity:.1f}")
            if stranded:
                st.error("🚨 Still stranded under CRREM.")
            else:
                st.success("✅ Compliant with CRREM pathway.")

        # Downloadable results
        result_df = pd.DataFrame([{
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
            "Stranded?": "Yes" if stranded else "No",
            "Asset Value (€)": asset_value,
            "Valuation Uplift (€)": uplift_value,
            "Carbon Saving (kg)": carbon_saving
        }])

        st.download_button("📥 Download Plan CSV", result_df.to_csv(index=False), file_name="transition_plan.csv")

    except Exception as e:
        st.error(f"💥 Processing error: {e}")
