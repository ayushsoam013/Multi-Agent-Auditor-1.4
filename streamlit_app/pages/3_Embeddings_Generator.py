import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Embeddings Generator", page_icon="🔢")

st.title("🔢 Embeddings Generator")

text_input = st.text_area("Enter text to embed", placeholder="Enter your text here...")
dimension = st.number_input("Dimension (Optional)", min_value=1, value=768)

if st.button("Generate Embedding"):
    if not text_input:
        st.error("Please enter some text.")
    else:
        with st.spinner("Generating..."):
            try:
                payload = {
                    "text": text_input,
                    "dimension": dimension
                }
                response = requests.post(f"{API_BASE_URL}/embeddings/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    vector = data.get("vector", [])
                    st.success(f"Generated vector with length {len(vector)}")
                    st.write(vector)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
