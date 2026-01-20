import streamlit as st
import requests
import json
import os

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")

st.title("💬 Chat with AI Models")

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")

# Provider Selection
# Fetch current provider from backend to sync or just let user override for this session?
# ideally we want per-request provider.
provider_options = ["gemini", "litellm"]
selected_provider = st.sidebar.selectbox("Select Provider", provider_options, index=0)

# Model Selection
# Load models from JSON files
# We'll use relative paths assuming we run from root? No, `streamlit run streamlit_app/app.py`
# We need to find the files. They are in `misc/`
# c:\Users\Imart\Documents\POC\Multi-Agent-Auditor-1.4\misc\gemini_models.json
# We should use absolute paths or relative to project root.
# Getting project root:
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
misc_dir = os.path.join(project_root, "misc")

gemini_models_path = os.path.join(misc_dir, "gemini_models.json")
litellm_models_path = os.path.join(misc_dir, "litellm_models.json")

models = []
if selected_provider == "gemini":
    if os.path.exists(gemini_models_path):
        with open(gemini_models_path, "r") as f:
            data = json.load(f)
            # Structure: {"models": [{"name": "models/gemini-pro", ...}]}
            models = [m["name"] for m in data.get("models", [])]
    else:
        st.error(f"Models file not found: {gemini_models_path}")
elif selected_provider == "litellm":
    if os.path.exists(litellm_models_path):
        with open(litellm_models_path, "r") as f:
            data = json.load(f)
            # Structure: {"data": [{"id": "openai/gpt-4", ...}]}
            models = [m["id"] for m in data.get("data", [])]
    else:
        st.error(f"Models file not found: {litellm_models_path}")

selected_model = st.sidebar.selectbox("Select Model", models)

# Parameters
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7)
max_tokens = st.sidebar.number_input("Max Output Tokens", min_value=1, max_value=32000, value=1000)

# System Prompt
system_prompt = st.sidebar.text_area("System Prompt", value="You are a helpful AI assistant.")

# --- Chat Interface ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "usage" in message:
            with st.expander("Token Usage"):
                st.json(message["usage"])

# User Input
if prompt := st.chat_input("What is up?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare payload
    # Construct messages list including system prompt if supported
    # If system prompt is supported, it usually goes as first message or specific field.
    # For simplicity, we'll prepend it if it's the first turn or just send it as system role (if backend supports)
    # Our backend just passes messages to provider.
    # Gemini supports "system_instruction" separately or just system message? 
    # Let's check `dtos.py` -> `ChatMessage`. It allows `role`.
    # We will prepend system prompt for every request or just maintain context?
    # Streamlit reruns script. We shouldn't duplicate system prompt.
    # We will construct the API payload messages from:
    # 1. System Prompt (as system role)
    # 2. Session messages
    
    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    payload = {
        "messages": api_messages,
        "model": selected_model,
        "provider": selected_provider,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_BASE_URL}/chat/completions", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"]
                    usage = data.get("usage")
                    
                    st.markdown(content)
                    if usage:
                        with st.expander("Token Usage"):
                            st.json(usage)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "model", # or assistant
                        "content": content,
                        "usage": usage
                    })
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
