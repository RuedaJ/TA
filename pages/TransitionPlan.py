
import streamlit as st
import pandas as pd

# Load mapping and uplift data
hvac_map = pd.read_excel("data/Technical_Systems_CRREM_Compatible.xlsx")
esg_val = pd.read_excel("data/ESG_Valuation_Impacts_CRREM_Compatible.xlsx")

st.set_page_config(page_title="📆 Transition Plan (HVAC & EPC)", layout="wide")
st.title("📆 ESG Transition Plan – HVAC + Valuation Impact")

with st.form("transition_inputs"):
    col1, col2, col3 = st.columns(3)
    asset_class = col1.selectbox("Asset Class", hvac_map["Asset Class"].unique())
    country_code = col2.selectbox("Country", esg_val["Country"].unique())
    current_system = col3.selectbox("Current HVAC System", hvac_map["Current System"].unique())
    new_system = st.selectbox("New HVAC System", hvac_map["New System"].unique())

    current_epc = st.selectbox("Current EPC Rating", ["G", "F", "E", "D", "C", "B", "A"])
    new_epc = st.selectbox("Target EPC Rating", ["G", "F", "E", "D", "C", "B", "A"], index=5)

    asset_value = st.number_input("Current Asset Value (€)", min_value=1000000, value=25000000)
    retrofit_year = st.slider("Planned Retrofit Year", 2024, 2035, 2025)
    submitted = st.form_submit_button("Evaluate Transition Plan")

if submitted:
    try:
        # Get capex cost from HVAC map
        hvac_row = hvac_map.query("`Asset Class` == @asset_class and `Current System` == @current_system and `New System` == @new_system").iloc[0]
        capex = hvac_row["CapEx (€)"]
        carbon_saving = hvac_row["Annual Carbon Saving (kgCO2e)"]
        energy_saving = hvac_row["Annual Energy Saving (kWh)"]

        # Get valuation uplift from ESG file
        uplift_row = esg_val.query("Country == @country_code and `From EPC` == @current_epc and `To EPC` == @new_epc").iloc[0]
        uplift_pct = uplift_row["Valuation Uplift (%)"]
        uplift_value = asset_value * (uplift_pct / 100)

        # Summary
        st.subheader("📊 Retrofit Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("CapEx Estimate", f"€{capex:,.0f}")
        col2.metric("Valuation Uplift", f"€{uplift_value:,.0f} ({uplift_pct:.1f}%)")
        col3.metric("Planned Year", retrofit_year)

        st.subheader("📉 Impact Forecast")
        st.markdown(f"- Estimated **Carbon Savings**: {carbon_saving:,.0f} kgCO₂e/year")
        st.markdown(f"- Estimated **Energy Savings**: {energy_saving:,.0f} kWh/year")

        result_df = pd.DataFrame([{
            "Asset Class": asset_class,
            "Country": country_code,
            "Current HVAC": current_system,
            "New HVAC": new_system,
            "Current EPC": current_epc,
            "New EPC": new_epc,
            "Asset Value (€)": asset_value,
            "Valuation Uplift (€)": uplift_value,
            "CapEx (€)": capex,
            "Carbon Saving (kgCO2e)": carbon_saving,
            "Energy Saving (kWh)": energy_saving,
            "Retrofit Year": retrofit_year
        }])

        st.download_button("📥 Download Transition Plan CSV", result_df.to_csv(index=False), file_name="transition_plan_summary.csv")

    except Exception as e:
        st.error(f"Error: {e}")
