
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configure Streamlit page
st.set_page_config(page_title="💰 ROI & Carbon Payback", layout="wide")
st.title("💰 Retrofit ROI + Carbon Payback Calculator")

# Load datasets
try:
    retrofit_costs = pd.read_excel("data/Retrofit_Costs_CRREM_Compatible.xlsx")
    tariffs = pd.read_excel("data/Utility_Tariffs_CRREM_Compatible.xlsx")
    discount_rates = pd.read_excel("data/Discount_Rates_Risk_Premiums_CRREM_Compatible.xlsx")
    energy_prices = pd.read_csv("data/Energy_Prices_CRREM_Compatible.csv")
    emission_factors = pd.read_csv("data/crrem_emission_factors.csv")
    crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
    baselines = pd.read_excel("data/Energy_Performance_Baselines_CRREM_Compatible.xlsx")
    archetypes = pd.read_excel("data/Building_Archetypes_CRREM_Compatible.xlsx")
except Exception as e:
    st.error(f"❌ Error loading input files: {e}")
    st.stop()

# Form Inputs
with st.form("roi_form"):
    st.subheader("🏗️ Asset Details")

    col1, col2, col3 = st.columns(3)
    country = col1.selectbox("Country", sorted(tariffs["Country"].dropna().unique()))
    asset_class = col2.selectbox("Asset Class", sorted(archetypes["Asset_Class"].dropna().unique()))
    vintage = col3.selectbox("Vintage", sorted(archetypes["Vintage"].dropna().unique()))

    match_typology = archetypes[
        (archetypes["Country_code_CRREM"] == country) &
        (archetypes["Asset_Class"] == asset_class) &
        (archetypes["Vintage"] == vintage)
    ]
    suggested_typology = match_typology.iloc[0]["Typology"] if not match_typology.empty else "N/A"

    col4, col5 = st.columns(2)
    st.markdown(f"📌 **Suggested Typology**: `{suggested_typology}`")
    retrofit_category = col4.selectbox("Retrofit Category", retrofit_costs["Retrofit Category"].dropna().unique())
    technology = col5.selectbox("Technology", retrofit_costs["Technology"].dropna().unique())

    col6, col7 = st.columns(2)
    fuel_type = col6.selectbox("Fuel Type", sorted(tariffs["Fuel Type"].dropna().unique()))
    floor_area = col7.number_input("Floor Area (m²)", min_value=100, value=1000)

    kwh_before = st.number_input("Annual Energy Use Before (kWh)", value=100000)
    kwh_after = st.number_input("Annual Energy Use After (kWh)", value=70000)
    year = st.slider("Start Year", 2024, 2035, 2025)

    submitted = st.form_submit_button("🔍 Calculate")

if submitted:
    try:
        # Fetch relevant rows
        capex_row = retrofit_costs.query("`Retrofit Category` == @retrofit_category and Technology == @technology").iloc[0]
        tariff_row = tariffs.query("Country == @country and `Fuel Type` == @fuel_type").iloc[0]
        discount_row = discount_rates.query("Country == @country").iloc[0]
        factor_row = emission_factors.query("country == @country and fuel == @fuel_type").iloc[0]
        price_row = energy_prices.query("Country == @country and Year == @year").iloc[0]

        capex_total = capex_row["Cost per m² (EUR)"] * floor_area
        discount_rate = discount_row["Discount Rate"]
        carbon_factor = factor_row["kgCO2/kWh"]
        price_per_kwh = price_row["Price_EUR_per_kWh"]

        savings_kwh = kwh_before - kwh_after
        annual_savings_eur = savings_kwh * price_per_kwh
        emissions_saved = savings_kwh * carbon_factor

        # Financial model
        cash_flows = np.array([-capex_total] + [annual_savings_eur] * 10)
        discounted = [cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows)]
        npv = sum(discounted)
        irr = np.irr(cash_flows)
        roi = (sum(cash_flows[1:]) - capex_total) / capex_total
        payback = capex_total / annual_savings_eur if annual_savings_eur > 0 else float("inf")

        # CRREM
        crrem_row = crrem_pathways.query("region_code == @country and asset_class == @asset_class and year == @year")
        crrem_target = crrem_row["target_carbon_intensity_kgco2m2"].values[0] if not crrem_row.empty else None
        actual_intensity = kwh_after / floor_area * carbon_factor
        stranded = crrem_target is not None and actual_intensity > crrem_target

        # Results
        st.subheader("📊 Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("NPV", f"€{npv:,.0f}")
        col2.metric("IRR", f"{irr*100:.1f}%" if not np.isnan(irr) else "N/A")
        col3.metric("Payback Period", f"{payback:.1f} yrs" if payback != float("inf") else "N/A")

        st.markdown(f"💨 **Emissions Reduction**: {emissions_saved:,.0f} kgCO₂/year")
        if crrem_target:
            st.markdown(f"📉 **Post-Retrofit Intensity**: {actual_intensity:.1f} vs CRREM target {crrem_target:.1f} kgCO₂/m²")
            if stranded:
                st.error("🚨 This asset remains **stranded** under CRREM.")
            else:
                st.success("✅ Retrofit meets CRREM decarbonization target.")

        # Cash flow chart
        st.subheader("📈 10-Year Cash Flow")
        fig, ax = plt.subplots()
        ax.bar(range(year, year + 10), [annual_savings_eur] * 10, color="#184999")
        ax.set_ylabel("Annual Savings (€)")
        ax.set_xlabel("Year")
        st.pyplot(fig)

        # Export
        st.download_button(
            "📥 Download ROI Table",
            pd.DataFrame({
                "Year": range(year, year + 10),
                "Savings (€)": [annual_savings_eur]*10,
                "Discounted (€)": discounted[1:]
            }).to_csv(index=False),
            file_name="roi_cashflow.csv"
        )

    except Exception as e:
        st.error(f"❌ Calculation error: {e}")
