import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from io import BytesIO

# File paths
DATA_DIR = "data/"
required_files = [
    "crrem_asset_classes.csv",
    "crrem_conversion_factors.csv",
    "crrem_emission_factors.csv",
    "crrem_country_codes.csv",
    "crrem_pathways.csv",
    "crrem_time_horizon.csv",
    "crrem_parameters_config.csv",
    "crrem_country_reference.csv"
]

# Check for missing files
missing = [f for f in required_files if not os.path.exists(os.path.join(DATA_DIR, f))]
if missing:
    st.error(f"Missing required data files: {missing}")
    st.stop()

# Load data
asset_classes = pd.read_csv(os.path.join(DATA_DIR, "crrem_asset_classes.csv"))
conversion_factors = pd.read_csv(os.path.join(DATA_DIR, "crrem_conversion_factors.csv"))
emission_factors = pd.read_csv(os.path.join(DATA_DIR, "crrem_emission_factors.csv"))
country_codes = pd.read_csv(os.path.join(DATA_DIR, "crrem_country_codes.csv"))
pathways = pd.read_csv(os.path.join(DATA_DIR, "crrem_pathways.csv"))
time_horizon = pd.read_csv(os.path.join(DATA_DIR, "crrem_time_horizon.csv"))
parameters_config = pd.read_csv(os.path.join(DATA_DIR, "crrem_parameters_config.csv"))
country_reference = pd.read_csv(os.path.join(DATA_DIR, "crrem_country_reference.csv"))

# Load archetype and EPC baseline datasets
try:
    archetypes = pd.read_excel(os.path.join(DATA_DIR, "Building_Archetypes_CRREM_Compatible.xlsx"))
    epc_baselines = pd.read_excel(os.path.join(DATA_DIR, "Energy_Performance_Baselines_CRREM_Compatible.xlsx"))
except Exception as e:
    st.warning(f"Optional data missing: {e}")

discount_rate = float(parameters_config[parameters_config['parameter'] == 'discount_rate']['default_value'].values[0])
payback_threshold = float(parameters_config[parameters_config['parameter'] == 'payback_years_threshold']['default_value'].values[0])

st.sidebar.header("Asset Inputs (Single or Batch)")
mode = st.sidebar.radio("Mode", ["Single Asset", "Batch Upload"])

if mode == "Single Asset":
    asset_class = st.sidebar.selectbox("Asset Class", asset_classes['asset_class'].unique())
    country_code = st.sidebar.selectbox("Country Code", country_codes['Code'].unique())

    # Archetype auto-fill toggle
    st.sidebar.subheader("Autofill from Archetype")
    if st.sidebar.checkbox("Enable Auto-Fill Inputs"):
        try:
            row = archetypes[(archetypes['country_code'] == country_code) & (archetypes['asset_class'] == asset_class)].iloc[0]
            floor_area = row['avg_floor_area']
            carbon_intensity = row['avg_carbon_intensity']
            st.sidebar.write(f"Auto-filled Floor Area: {floor_area} m²")
            st.sidebar.write(f"Auto-filled Carbon Intensity: {carbon_intensity} kgCO₂/m²")
        except:
            floor_area = 1000.0
            carbon_intensity = 85.0
            st.warning("No archetype match found. Using defaults.")
    else:
        carbon_intensity = st.sidebar.number_input("Current Carbon Intensity (kgCO2/m²)", min_value=0.0, value=85.0)
        floor_area = st.sidebar.number_input("Floor Area (m²)", min_value=1.0, value=1000.0)

    capex = st.sidebar.number_input("CapEx (€)", min_value=0.0, value=250 * floor_area)
    tenant_ratio = st.sidebar.slider("Tenant Share (%)", min_value=0, max_value=100, value=30)

    region = country_reference[country_reference['country_code'] == country_code]['crrem_region'].values[0]
    target_pathway = pathways[(pathways['region_code'] == region) & (pathways['asset_class'] == asset_class)]
    if target_pathway.empty:
        st.error("No pathway found for this asset/country combo.")
        st.stop()

    year = target_pathway['year'].values[0]
    target_intensity = target_pathway['target_carbon_intensity_kgco2m2'].values[0]
    delta = carbon_intensity - target_intensity
    stranding_year = year if delta > 0 else None
    retrofit_year = year - 5 if stranding_year else None
    advice = "Retrofit recommended" if capex > payback_threshold else "No immediate retrofit"

    st.subheader("Stranding Results")
    st.write(f"**Stranding Year**: {stranding_year}")
    st.write(f"**Delta to Target**: {delta:.2f}")
    st.write(f"**Recommended Retrofit Year**: {retrofit_year}")
    st.write(f"**Advice**: {advice}")

    st.subheader("Cost Split")
    st.write({
        "Total CapEx (€)": capex,
        "Tenant Share (€)": capex * (tenant_ratio / 100),
        "Landlord Share (€)": capex * (1 - tenant_ratio / 100)
    })

    years = np.arange(2020, 2050, 5)
    actual = [carbon_intensity] * len(years)
    target = [target_intensity] * len(years)
    fig, ax = plt.subplots()
    ax.plot(years, actual, '--o', label="Asset Intensity")
    ax.plot(years, target, '-x', label="CRREM Target")
    ax.set_title("Carbon Intensity vs Target")
    ax.set_xlabel("Year")
    ax.set_ylabel("kgCO2/m²")
    ax.legend()
    st.pyplot(fig)

else:
    st.subheader("Batch Processing")
    uploaded_file = st.file_uploader("Upload CSV with: asset_class, country_code, carbon_intensity, floor_area", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        results = []

        for _, row in df.iterrows():
            try:
                region = country_reference[country_reference['country_code'] == row['country_code']]['crrem_region'].values[0]
                target_pathway = pathways[(pathways['region_code'] == region) & (pathways['asset_class'] == row['asset_class'])]

                if target_pathway.empty:
                    raise ValueError("Missing pathway")

                year = target_pathway['year'].values[0]
                target_intensity = target_pathway['target_carbon_intensity_kgco2m2'].values[0]
                delta = row['carbon_intensity'] - target_intensity
                stranding_year = year if delta > 0 else None
                retrofit_year = year - 5 if stranding_year else None
                capex = row.get('capex', row['floor_area'] * 250)
                tenant_share = capex * 0.3

                results.append({
                    **row,
                    'stranding_year': stranding_year,
                    'delta_to_target': delta,
                    'recommended_retrofit_year': retrofit_year,
                    'tenant_share': tenant_share,
                    'landlord_share': capex - tenant_share
                })
            except Exception as e:
                results.append({**row, 'error': str(e)})

        df_results = pd.DataFrame(results)
        st.dataframe(df_results)

        # Export buttons
        excel_buffer = BytesIO()
        df_results.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button("Download as Excel", data=excel_buffer, file_name="crrem_batch_results.xlsx")

        json_data = df_results.to_json(orient="records", indent=2)
        st.download_button("Download as JSON", data=json_data, file_name="crrem_batch_results.json")

# -------------------- HTML Export Buttons --------------------

st.markdown("---")
st.subheader("📤 Export Reports as HTML")

# CRREM results to HTML
if 'df_results' in locals():
    html_crrem = df_results.to_html(index=False)
    st.download_button(
        label="📄 Download CRREM Results as HTML",
        data=html_crrem,
        file_name="crrem_results.html",
        mime="text/html"
    )

# ROI results to HTML if available
if 'roi_df' in locals():
    html_roi = roi_df.to_html(index=False)
    st.download_button(
        label="📄 Download ROI Results as HTML",
        data=html_roi,
        file_name="roi_results.html",
        mime="text/html"
    )

# Transition plan summary (sample output)
if 'asset_class' in locals() and 'stranding_year' in locals():
    transition_summary = f"""
    <h2>Transition Plan Summary</h2>
    <ul>
      <li><b>Asset Class:</b> {asset_class}</li>
      <li><b>Stranding Year:</b> {stranding_year}</li>
      <li><b>Recommended Retrofit Year:</b> {retrofit_year}</li>
      <li><b>Advice:</b> {advice}</li>
    </ul>
    """
    st.download_button(
        label="📄 Download Transition Plan as HTML",
        data=transition_summary,
        file_name="transition_plan.html",
        mime="text/html"
    )