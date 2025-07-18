
# 📚 CRREM-Compatible Data Catalog

This catalog outlines the purpose and current usage status of each file in the `/data` directory.

| File | Purpose | Used In Tool | Tool/Feature |
|------|---------|--------------|--------------|
| `crrem_asset_classes.csv` | Asset class definitions | ✅ | CRREM |
| `crrem_country_codes.csv` | ISO to CRREM region mapping | ✅ | CRREM |
| `crrem_pathways.csv` | Emissions trajectory targets | ✅ | CRREM |
| `crrem_parameters_config.csv` | Toolkit-level config (discount rates, payback) | ✅ | CRREM, ROI |
| `crrem_conversion_factors.csv` | kWh to CO₂ conversion | ✅ | ROI |
| `crrem_emission_factors.csv` | General carbon emissions | ✅ | ROI |
| `Energy_Prices_CRREM_Compatible.csv` | Energy prices by country | ✅ | ROI |
| `Retrofit_Costs_CRREM_Compatible.xlsx` | CapEx assumptions by intervention | 🔄 Ready | ROI, Transition Plan |
| `Building_Archetypes_CRREM_Compatible.xlsx` | Pre-fill inputs by archetype | 🔄 Ready | CRREM, ROI |
| `Utility_Tariffs_CRREM_Compatible.xlsx` | Tenant-focused billing rates | 🔄 Ready | ROI, Green Lease |
| `Technical_Systems_CRREM_Compatible.xlsx` | Links retrofits to HVAC systems | 🔄 Ready | Transition Plan |
| `Energy_Performance_Baselines_CRREM_Compatible.xlsx` | Typical EPC carbon levels | 🔄 Ready | CRREM |
| `ESG_Valuation_Impacts_CRREM_Compatible.xlsx` | Value delta by carbon/EPC class | 🔄 Ready | Valuation Sensitivity Tool |
| `Utility_Emission_Factors_CRREM_Compatible.xlsx` | Scope 2 emissions per utility | 🔮 Future | ROI |
| `Discount_Rates_Risk_Premiums_CRREM_Compatible.xlsx` | Custom discount rates by sector | 🔄 Ready | ROI |
| `Cost_Escalation_Factors_CRREM_Compatible.xlsx` | CapEx inflation forecast | 🔄 Ready | ROI |
| `Embodied_Carbon_Benchmarks_CRREM_Compatible.xlsx` | Benchmarks for lifecycle CO₂ | 🔮 Future | Embodied Carbon Model |
| `Refrigerant_GWP_Factors_CRREM_Compatible.xlsx` | HVAC GHG intensity | 🔮 Future | Scope 1 Analysis |
| `Refrigerant_Leakage_Rates_CRREM_Compatible.xlsx` | Annual loss assumptions | 🔮 Future | Scope 1 Analysis |
| `Heating_Emissions_Factors_CRREM_Compatible.xlsx` | System-level heating emissions | 🔮 Future | ROI Detail |
| `Cooling_Emissions_Factors_CRREM_Compatible.xlsx` | System-level cooling emissions | 🔮 Future | ROI Detail |
| `Electricity_Emissions_Factors_CRREM_Compatible.xlsx` | Grid emissions by year | 🔮 Future | ROI |
| `Carbon_Pricing_CRREM_Compatible.xlsx` | CO₂ pricing for payback logic | 🔮 Future | Scenario Engine |
| `Carbon_Pricing_Scenarios_CRREM_Compatible.xlsx` | Shadow pricing assumptions | 🔮 Future | Scenario Engine |
| `Renewable_Energy_Supply_Scenarios_CRREM_Compatible.xlsx` | RE integration impact | 🔮 Future | Embodied Model |
| `Reference_Utility_Intensities_CRREM_Compatible.xlsx` | Utility demand per archetype | 🔮 Future | ROI Baseline |
| `ESG_Lending_Terms_CRREM_Compatible.xlsx` | Green loan lending inputs | 🔮 Future | Financing Tool |
| `Financing_Conditions_CRREM_Compatible.xlsx` | Risk/return assumptions | 🔮 Future | Scenario Engine |
| `Utility_Costs_CRREM_Compatible.xlsx` | Alt to energy prices (tenant view) | ⚠️ Redundant | ROI |

Legend: ✅ = Used | 🔄 = Ready | 🔮 = For Future Tool | ⚠️ = Possibly Duplicated
