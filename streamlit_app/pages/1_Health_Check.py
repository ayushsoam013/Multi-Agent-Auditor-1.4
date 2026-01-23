# Monitoring dashboard for system health.
# Periodically pings backend endpoints to verify connectivity and API key status.
import streamlit as st
import requests
import sys
import os

# Add parent directory to path to allow importing shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sidebar import render_sidebar

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Health Check", page_icon="🏥")

# Render common sidebar elements
render_sidebar()

st.title("🏥 Service Health Check")


def check_health(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/health/{endpoint}")
        if response.status_code == 200:
            return "✅ Healthy", response.json()
        else:
            return f"❌ Error {response.status_code}", response.json()
    except Exception as e:
        return "❌ Offline", str(e)


col1, col2 = st.columns(2)

with col1:
    st.subheader("FastAPI Server")
    status, details = check_health("server")
    st.write(status)
    if status.startswith("✅"):
        st.json(details)

with col2:
    st.subheader("Gemini Service")
    status, details = check_health("gemini")
    st.write(status)
    if status.startswith("✅"):
        st.json(details)


if st.button("Refresh status"):
    st.rerun()
