
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data files
retrofit_costs = pd.read_excel("data/Retrofit_Costs_CRREM_Compatible.xlsx")
utility_tariffs = pd.read_excel("data/Utility_Tariffs_CRREM_Compatible.xlsx")
discount_rates = pd.read_excel("data/Discount_Rates_Risk_Premiums_CRREM_Compatible.xlsx")

st.set_page_config(page_title="💰 ROI & Carbon Payback Tool", layout="wide")
st.title("💰 Retrofit ROI + Carbon Payback Calculator")

with st.form("roi_inputs"):
    asset_class = st.selectbox("Asset Class (from CRREM)", ['Office', 'Retail', 'Residential'])
    col1, col2, col3 = st.columns(3)
    retrofit_category = col1.selectbox("Retrofit Category", retrofit_costs["Retrofit Category"].unique())
    technology = col2.selectbox("Technology", retrofit_costs["Technology"].unique())
    country = col3.selectbox("Country", utility_tariffs["Country"].unique())
    fuel_type = st.selectbox("Fuel Type", utility_tariffs["Fuel Type"].unique())

    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=1000)
    kwh_before = st.number_input("Energy Use Before (kWh)", min_value=1000, value=100000)
    kwh_after = st.number_input("Energy Use After (kWh)", min_value=100, value=60000)
    year = st.slider("Start Year", 2024, 2035, value=2025)
    use_tenant_split = st.checkbox("Apply tenant/landlord split?", value=True)
    user_discount_override = st.number_input("Override Discount Rate (%)", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Calculate ROI")

if submitted:
    try:
        # Get retrofit cost data
        capex_row = retrofit_costs.query("`Retrofit Category` == @retrofit_category and Technology == @technology").iloc[0]
        capex = capex_row["Cost per m² (EUR)"] * floor_area

        # Get utility and discount data
        tariff_row = utility_tariffs.query("Country == @country and `Fuel Type` == @fuel_type").iloc[0]
        discount_row = discount_rates.query("Country == @country").iloc[0]

        tariff = tariff_row["Landlord Tariff"] if use_tenant_split else tariff_row["Blended Tariff"]
        discount_rate = user_discount_override / 100 if user_discount_override > 0 else discount_row["Discount Rate"]

        # Calculations
        savings_kwh = kwh_before - kwh_after
        annual_savings = savings_kwh * tariff
        emissions_saved = savings_kwh * tariff_row["Carbon Factor"]

        # Cash flow model
        years = list(range(year, year + 10))
        savings_series = np.array([annual_savings / ((1 + discount_rate) ** (i - year)) for i in years])
        npv = savings_series.sum() - capex
        irr = np.irr([-capex] + [annual_savings] * 10)
        roi = (annual_savings * 10 - capex) / capex
        payback_years = capex / annual_savings if annual_savings else float('inf')

        
    # CRREM Pathway Alignment Check
    try:
        crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
        pathway_row = crrem_pathways.query("asset_class == @asset_class and region_code == @country and year == @year").iloc[0]
        target_intensity = pathway_row["target_carbon_intensity_kgco2m2"]

        intensity_after = kwh_after / floor_area * tariff_row["Carbon Factor"]  # Estimate kgCO₂/m²
        stranded = intensity_after > target_intensity

        st.subheader("📌 CRREM Alignment")
        if stranded:
            st.error(f"🚨 Post-retrofit intensity ({intensity_after:.1f} kgCO₂/m²) EXCEEDS CRREM target ({target_intensity:.1f}).")
        else:
            st.success(f"✅ Post-retrofit intensity ({intensity_after:.1f} kgCO₂/m²) is BELOW CRREM target ({target_intensity:.1f}).")

    except Exception as e:
        st.warning(f"CRREM pathway comparison unavailable: {e}")

    # Output
        col1, col2, col3 = st.columns(3)
        col1.metric("NPV", f"€{npv:,.0f}")
        col2.metric("IRR", f"{irr*100:.1f}%")
        col3.metric("Payback", f"{payback_years:.1f} years")

        st.subheader("📈 Annual Cash Flow Projection")
        fig, ax = plt.subplots()
        ax.bar(years, [annual_savings]*10, color="#184999")
        ax.axhline(0, color="black")
        ax.set_xlabel("Year")
        ax.set_ylabel("Annual Savings (€)")
        ax.set_title("Cash Flow Projection")
        st.pyplot(fig)

        st.markdown(f"**Estimated Emissions Reduction**: {emissions_saved:,.0f} kgCO₂e over 10 years")
        st.download_button("📥 Download Cash Flow Table", pd.DataFrame({
            "Year": years,
            "Discounted Savings (€)": savings_series
        }).to_csv(index=False), file_name="roi_cash_flow.csv")

    except Exception as e:
        st.error(f"Error: {e}")
