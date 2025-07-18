
# 🏢 SIERA ESG Platform

A full-stack, open-source ESG analytics and transition planning platform built with Streamlit and Python. Designed to emulate key features of tools like SIERA by EVORA and CRREM.

---

## 🚀 Features

- ✅ CSV Upload with Schema Validation
- 📊 Portfolio Dashboard (KPIs: carbon, energy, stranding year)
- 📉 CRREM-Compliant Stranding Risk Plots
- 📘 Stakeholder Playbooks (Investor View)
- 📆 Net Zero Transition Plan with Yearly Emissions Simulator
- 🧠 AI Assistant to explain ESG metrics to non-technical users

---

## 📁 Project Structure

```
streamlit_app/             # Streamlit pages
backend/
├── calculators/           # ESG calculators (CRREM logic)
├── utils/                 # Validators
└── config/                # Parameters & settings
data/                      # CRREM-compatible reference files
static/                    # Optional logos, templates
```

---

## 🧪 Sample Input Files

### `assets.csv`

| Asset Name | Floor Area (m²) | Carbon Intensity (kgCO2e/m²) | EPC Rating | Energy Consumption (kWh) |

### `utilities.csv`

| Asset Name | Month | Energy Consumption (kWh) | Water Consumption (m³) | Waste (kg) |

---

## 🧠 Run Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app/Home.py
```

---

## 📤 Streamlit Cloud Deployment

1. Upload to GitHub
2. Connect GitHub repo in [Streamlit Cloud](https://share.streamlit.io)
3. Set entry file: `streamlit_app/Home.py`
4. Done!

---

## ⚠️ Limitations

- No persistent DB (in-memory only)
- Only rule-based AI assistant (no external API)
- Embodied carbon, role-based login, and GRESB exports are future work

---

## 📅 Roadmap

- [x] MVP ESG Tools
- [x] Stakeholder Dashboards
- [x] Net Zero Planning
- [x] AI Assistant (light)
- [ ] API/LLM Integration (optional)
- [ ] Full ESG Playbooks + Reports
