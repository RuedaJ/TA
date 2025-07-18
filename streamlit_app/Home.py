
import streamlit as st

st.set_page_config(page_title="SIERA ESG Platform", layout="wide")

st.sidebar.title("🔍 ESG Navigation")
page = st.sidebar.radio(
    "Go to:",
    [
        "🏠 Home",
        "📂 Upload ESG Data",
        "📊 ESG Dashboard",
        "📉 CRREM Calculator",
        "💰 ROI & Payback Tool",
        "📆 Transition Plan",
        "📘 Stakeholder Playbooks",
    ],
)

st.title("🏠 Welcome to the SIERA ESG Data Platform")

st.markdown("""
This platform helps real estate and infrastructure stakeholders assess:
- Carbon risk and CRREM-aligned stranding years
- Retrofit payback periods and NPV
- ESG KPIs like carbon intensity and energy use
- Transition pathways and valuation uplift
""")
