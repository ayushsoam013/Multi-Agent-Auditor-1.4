import streamlit as st
import requests
import pandas as pd
import time
import os

st.set_page_config(page_title="Bulk Audit Dashboard", layout="wide")

st.title("📦 Bulk Audit Dashboard")
st.markdown("""
Manage and monitor large-scale product audits. 
The system processes products from `misc/input_data.csv` and saves results to `misc/audit_results.csv`.
""")

# API Base URL - In a real setup, this would come from settings
API_BASE = "http://localhost:8000/api/v1/bulk-audit"


def get_status():
    try:
        response = requests.get(f"{API_BASE}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None


def run_bulk(limit):
    try:
        response = requests.post(f"{API_BASE}/run", params={"limit": limit}, timeout=10)
        if response.status_code == 200:
            st.success("Bulk audit started successfully!")
            st.rerun()
        elif response.status_code == 409:
            st.warning("Bulk audit is already in progress.")
        else:
            st.error(f"Error starting audit: {response.text}")
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")


# Sidebar - Controls
st.sidebar.header("Controls")
limit = st.sidebar.number_input("Batch Limit", min_value=1, max_value=10000, value=5)
if st.sidebar.button("🚀 Start Bulk Audit"):
    run_bulk(limit)

auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=False)

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Main Content - Metrics
status = get_status()

if status:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Items", status["total_items"])
    col2.metric("Processed", status["processed_items"])
    col3.metric("Success Rate", f"{status['success_rate']:.1f}%")
    col4.metric("Total Cost", f"${status['total_cost']:.4f}")

    st.progress(min(status["progress_percentage"] / 100.0, 1.0))
    st.caption(
        f"Progress: {status['progress_percentage']:.2f}% ({status['processed_items']}/{status['total_items']})"
    )

    # Detailed Table
    st.subheader("Recent Results")
    results_path = "misc/audit_results.csv"
    if os.path.exists(results_path):
        try:
            df_results = pd.read_csv(results_path)
            # Display last 50 results
            st.dataframe(df_results.tail(50), use_container_width=True)

            # Download button
            csv = df_results.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Full Results CSV",
                data=csv,
                file_name="audit_results.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Error loading results: {e}")
    else:
        st.info("No results found yet. Start an audit to see data here.")
else:
    st.warning(
        "⚠️ Could not connect to the backend. Please ensure `python run_fast.py` is running."
    )
    st.info(
        "If you are running this for the first time, you might need to start the backend server."
    )

# Auto-refresh logic
if auto_refresh:
    time.sleep(5)
    st.rerun()
