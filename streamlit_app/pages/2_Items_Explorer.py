import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Items Explorer", page_icon="🔍", layout="wide")

st.title("🔍 Items Explorer")

collection_name = st.sidebar.text_input("Collection Name", value="product_data")
limit = st.sidebar.slider("Limit", min_value=1, max_value=100, value=10)

if st.button("Fetch Items"):
    with st.spinner(f"Fetching items from {collection_name}..."):
        try:
            params = {
                "collection_name": collection_name,
                "limit": limit,
                "with_payload": True,
                "with_vectors": False
            }
            response = requests.get(f"{API_BASE_URL}/items/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    # Flatten the structure for pandas
                    flattened_data = []
                    for item in items:
                        row = {"id": item["id"]}
                        row.update(item["payload"])
                        flattened_data.append(row)
                    
                    df = pd.DataFrame(flattened_data)
                    st.success(f"Found {len(items)} items.")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No items found in this collection.")
            else:
                st.error(f"Failed to fetch data: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
