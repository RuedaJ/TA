
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
    col1, col2, col3 = st.columns(3)
    asset_class = col1.selectbox("Asset Class", retrofit_costs["Asset Class"].unique())
    country = col2.selectbox("Country", utility_tariffs["Country"].unique())
    fuel_type = col3.selectbox("Fuel Type", utility_tariffs["Fuel Type"].unique())

    intervention = st.selectbox("Intervention Type", retrofit_costs["Intervention"].unique())
    floor_area = st.number_input("Floor Area (m²)", min_value=100, value=1000)
    kwh_before = st.number_input("Energy Use Before (kWh)", min_value=1000, value=100000)
    kwh_after = st.number_input("Energy Use After (kWh)", min_value=100, value=60000)
    year = st.slider("Start Year", 2024, 2035, value=2025)
    use_tenant_split = st.checkbox("Apply tenant/landlord split?", value=True)
    user_discount_override = st.number_input("Override Discount Rate (%)", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Calculate ROI")

if submitted:
    # Get data from tables
    capex_row = retrofit_costs.query("`Asset Class` == @asset_class and Intervention == @intervention").iloc[0]
    tariff_row = utility_tariffs.query("Country == @country and `Fuel Type` == @fuel_type").iloc[0]
    discount_row = discount_rates.query("Country == @country").iloc[0]

    # Calculations
    capex = capex_row["Cost per m²"] * floor_area
    tariff = tariff_row["Landlord Tariff"] if use_tenant_split else tariff_row["Blended Tariff"]
    discount_rate = user_discount_override / 100 if user_discount_override > 0 else discount_row["Discount Rate"]

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

    # Results
    st.markdown(f"**Estimated Emissions Reduction**: {emissions_saved:,.0f} kgCO₂e over 10 years")
    st.download_button("📥 Download Cash Flow Table", pd.DataFrame({
        "Year": years,
        "Discounted Savings (€)": savings_series
    }).to_csv(index=False), file_name="roi_cash_flow.csv")
