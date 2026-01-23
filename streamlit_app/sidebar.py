# Shared UI component for the Streamlit sidebar.
# Handles global state such as the active LLM provider (Gemini vs LiteLLM)
# and synchronizes settings with the FastAPI backend.
import os
import time
import streamlit as st
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def render_sidebar():
    """
    Renders the shared sidebar elements, specifically the LLM provider switcher.
    """
    st.sidebar.markdown("### Settings")

    provider_options = ["gemini", "litellm"]

    # Use session state to avoid fetching from backend on every rerun
    if "current_provider" not in st.session_state:
        try:
            current_provider_resp = requests.get(
                f"{API_BASE_URL}/config/provider", timeout=1
            )
            if current_provider_resp.status_code == 200:
                st.session_state.current_provider = current_provider_resp.json().get(
                    "provider", "litellm"
                )
            else:
                st.session_state.current_provider = "litellm"
        except Exception:
            st.session_state.current_provider = "litellm"

    current_provider = st.session_state.current_provider

    # 2. Display Selector
    try:
        index = provider_options.index(current_provider)
    except ValueError:
        index = 0

    selected_provider = st.sidebar.selectbox(
        "Select LLM Provider",
        options=provider_options,
        index=index,
        key="llm_provider_selector",
    )

    # 3. Handle Change
    if selected_provider != current_provider:
        try:
            response = requests.post(
                f"{API_BASE_URL}/config/provider",
                json={"provider": selected_provider},
                timeout=5,
            )
            if response.status_code == 200:
                st.session_state.current_provider = selected_provider
                st.sidebar.success(f"Switched to {selected_provider}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.sidebar.error("Failed to switch provider")
        except Exception as e:
            st.sidebar.error(f"Error switching provider: {e}")

    st.sidebar.divider()
