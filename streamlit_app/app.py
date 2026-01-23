# Main entry point for the Streamlit administration dashboard.
# Coordinates navigation and common UI elements across all pages.
import os
import streamlit as st
import requests
from sidebar import render_sidebar

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="Embeddings Optimization Admin", page_icon="🚀", layout="wide"
)

# Render common sidebar elements
render_sidebar()

st.title("🚀 Embeddings Optimization Admin")
st.markdown("""
Welcome to the administration panel for the Embeddings Optimization POC.

### Features:
- **Health Check**: Monitor the status of FastAPI, Gemini, and Qdrant.
- **Items Explorer**: Visualize items stored in Qdrant collections.

Use the sidebar to navigate between different tools.
""")

st.sidebar.success("Select a tool above.")
