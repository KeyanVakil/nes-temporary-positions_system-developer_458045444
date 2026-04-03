import streamlit as st

st.set_page_config(
    page_title="DrillSense Monitor",
    page_icon="🔧",
    layout="wide",
)

# Route based on query params
params = st.query_params
if "device" in params:
    from dashboard.pages.device import render
    render(params["device"])
else:
    from dashboard.pages.overview import render
    render()
