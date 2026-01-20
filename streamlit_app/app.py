import os
import streamlit as st
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="Embeddings Optimization Admin",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Embeddings Optimization Admin")
st.markdown("""
Welcome to the administration panel for the Embeddings Optimization POC.

### Features:
- **Health Check**: Monitor the status of FastAPI, Gemini, and Qdrant.
- **Items Explorer**: Visualize items stored in Qdrant collections.

Use the sidebar to navigate between different tools.
""")

current_provider = "litellm"

provider_options = ["gemini", "litellm"]

selected_provider = st.sidebar.selectbox(
    "Select LLM Provider", 
    options=provider_options, 
    index=provider_options.index(current_provider) if current_provider in provider_options else 0
)

# Provider Selection
try:
    current_provider_resp = requests.get(f"{API_BASE_URL}/config/provider")
    if current_provider_resp.status_code == 200:
        current_provider = current_provider_resp.json().get("provider", "litellm")
    else:
        current_provider = "litellm"
except:
    current_provider = "litellm"

if selected_provider != current_provider:
    try:
        response = requests.post(f"{API_BASE_URL}/config/provider", json={"provider": selected_provider})
        if response.status_code == 200:
            st.sidebar.success(f"Switched to {selected_provider}")
            st.rerun()
        else:
            st.sidebar.error("Failed to switch provider")
    except Exception as e:
        st.sidebar.error(f"Error switching provider: {e}")

st.sidebar.success("Select a tool above.")
