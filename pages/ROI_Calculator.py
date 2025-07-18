
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="💰 ROI & Carbon Payback Tool", layout="wide")
st.title("💰 Retrofit ROI + Carbon Payback Calculator")

# Load all necessary data
try:
    retrofit_costs = pd.read_excel("data/Retrofit_Costs_CRREM_Compatible.xlsx")
    utility_tariffs = pd.read_excel("data/Utility_Tariffs_CRREM_Compatible.xlsx")
    discount_rates = pd.read_excel("data/Discount_Rates_Risk_Premiums_CRREM_Compatible.xlsx")
    crrem_pathways = pd.read_csv("data/crrem_pathways.csv")
    crrem_assets = pd.read_csv("data/crrem_asset_classes.csv")
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

with st.form("roi_inputs"):
    st.subheader("📥 Retrofit Scenario Inputs")

    col1, col2, col3 = st.columns(3)
    asset_class = col1.selectbox("Asset Class (CRREM)", crrem_assets["asset_class"].dropna().unique())
    retrofit_category = col2.selectbox("Retrofit Category", retrofit_costs["Retrofit Category"].unique())
    technology = col3.selectbox("Technology", retrofit_costs["Technology"].unique())

    col4, col5, col6 = st.columns(3)
    country = col4.selectbox("Country", utility_tariffs["Country"].unique())
    fuel_type = col5.selectbox("Fuel Type", utility_tariffs["Fuel Type"].unique())
    floor_area = col6.number_input("Floor Area (m²)", min_value=100, value=1000)

    kwh_before = st.number_input("Energy Use Before (kWh)", min_value=1000, value=100000)
    kwh_after = st.number_input("Energy Use After (kWh)", min_value=100, value=60000)
    year = st.slider("Start Year", 2024, 2035, value=2025)

    use_tenant_split = st.checkbox("Apply tenant/landlord split?", value=True)
    user_discount_override = st.number_input("Override Discount Rate (%)", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Calculate ROI")

if submitted:
    try:
        # Lookup cost, tariff, discount
        capex_row = retrofit_costs.query("`Retrofit Category` == @retrofit_category and Technology == @technology").iloc[0]
        tariff_row = utility_tariffs.query("Country == @country and `Fuel Type` == @fuel_type").iloc[0]
        discount_row = discount_rates.query("Country == @country").iloc[0]

        capex = capex_row["Cost per m² (EUR)"] * floor_area
        tariff = tariff_row["Landlord Tariff"] if use_tenant_split else tariff_row["Blended Tariff"]
        discount_rate = user_discount_override / 100 if user_discount_override > 0 else discount_row["Discount Rate"]

        # ROI calculations
        savings_kwh = kwh_before - kwh_after
        annual_savings = savings_kwh * tariff
        emissions_saved = savings_kwh * tariff_row["Carbon Factor"]

        years = list(range(year, year + 10))
        savings_series = np.array([annual_savings / ((1 + discount_rate) ** (i - year)) for i in years])
        npv = savings_series.sum() - capex
        irr = np.irr([-capex] + [annual_savings] * 10)
        roi = (annual_savings * 10 - capex) / capex
        payback_years = capex / annual_savings if annual_savings else float('inf')

        # CRREM comparison
        try:
            pathway_row = crrem_pathways.query("asset_class == @asset_class and region_code == @country and year == @year").iloc[0]
            target_intensity = pathway_row["target_carbon_intensity_kgco2m2"]
            intensity_after = kwh_after / floor_area * tariff_row["Carbon Factor"]
            stranded = intensity_after > target_intensity
        except Exception as e:
            target_intensity = None
            stranded = None
            crrem_error = str(e)

        # Results Display
        st.subheader("📊 Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("NPV", f"€{npv:,.0f}")
        col2.metric("IRR", f"{irr*100:.1f}%" if not np.isnan(irr) else "N/A")
        col3.metric("Payback", f"{payback_years:.1f} years")

        st.markdown(f"**Estimated Emissions Reduction**: {emissions_saved:,.0f} kgCO₂e")

        st.subheader("📈 Annual Cash Flow Projection")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.bar(years, [annual_savings]*10, color="#184999")
        ax.axhline(0, color="black")
        ax.set_xlabel("Year")
        ax.set_ylabel("Annual Savings (€)")
        ax.set_title("Cash Flow Projection")
        st.pyplot(fig)

        if target_intensity:
            st.subheader("📌 CRREM Pathway Check")
            if stranded:
                st.error(f"🚨 Post-retrofit intensity ({intensity_after:.1f}) exceeds CRREM target ({target_intensity:.1f})")
            else:
                st.success(f"✅ Retrofit aligns with CRREM target ({target_intensity:.1f} kgCO₂/m²)")

        st.download_button("📥 Download Cash Flow CSV", pd.DataFrame({
            "Year": years,
            "Discounted Savings (€)": savings_series
        }).to_csv(index=False), file_name="roi_cash_flow.csv")

    except Exception as e:
        st.error(f"Calculation error: {e}")
