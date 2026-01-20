import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Health Check", page_icon="🏥")

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

col1, col2, col3 = st.columns(3)

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

with col3:
    st.subheader("Qdrant Service")
    status, details = check_health("qdrant")
    st.write(status)
    if status.startswith("✅"):
        st.json(details)

if st.button("Refresh status"):
    st.rerun()
