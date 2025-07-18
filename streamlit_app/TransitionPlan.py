
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import tempfile
from backend.utils.file_validator import validate_csv

st.set_page_config(layout="wide")
st.title("📆 Net Zero Transition Plan")

st.markdown("Upload your validated asset CSV to plan retrofits and visualize your decarbonization pathway.")

uploaded_file = st.file_uploader("Upload validated asset CSV", type=["csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    result = validate_csv(tmp_path, "assets")

    if result["status"] == "success":
        df = result["data"]

        # Allow user to define retrofit year per asset
        st.subheader("🛠️ Select Retrofit Year for Each Asset")
        retrofit_years = {}
        for asset in df["Asset Name"]:
            retrofit_years[asset] = st.selectbox(
                f"Retrofit year for {asset}",
                options=list(range(2024, 2036)),
                index=0,
                key=f"year_{asset}"
            )

        # Simulate emissions over time
        years = list(range(2024, 2036))
        emissions_by_year = {year: 0 for year in years}

        for _, row in df.iterrows():
            base_emission = row["Carbon Intensity (kgCO2e/m²)"] * row["Floor Area (m²)"]
            reduction = 0.4  # 40% carbon cut after retrofit (placeholder)
            asset_year = retrofit_years[row["Asset Name"]]
            for year in years:
                if year < asset_year:
                    emissions_by_year[year] += base_emission
                else:
                    emissions_by_year[year] += base_emission * (1 - reduction)

        emissions_series = pd.Series(emissions_by_year)

        st.subheader("📉 Projected Portfolio Emissions (kgCO2e)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=emissions_series.index, y=emissions_series.values,
                                 mode='lines+markers', name='Projected Emissions'))
        fig.update_layout(xaxis_title="Year", yaxis_title="Total Emissions (kgCO2e)",
                          title="Decarbonization Pathway")
        st.plotly_chart(fig)

        # Export data
        output_df = pd.DataFrame({
            "Year": emissions_series.index,
            "Total Emissions (kgCO2e)": emissions_series.values
        })
        st.download_button("Download Emissions Pathway CSV", output_df.to_csv(index=False),
                           file_name="transition_plan_emissions.csv")

    else:
        st.error(result["message"])
