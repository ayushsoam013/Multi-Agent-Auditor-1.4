# Main interactive tool for running the Multi-Agent Audit.
# Visualizes the pipeline execution in real-time, showing parallel and sequential steps.
import streamlit as st
import requests
import json
import time
import sys
import os

# Add parent directory to path to allow importing shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sidebar import render_sidebar

API_BASE_URL = "http://localhost:8000/api/v1"
APP_BASE_URL = "http://localhost:8501" # Adjust if running on different port
USD_TO_INR = 92


def format_inr(usd_amount):
    return f"₹{usd_amount * USD_TO_INR:.4f}"


st.set_page_config(page_title="Multi-Agent Auditor", page_icon="🤖", layout="wide")

# Render common sidebar elements
render_sidebar()

# Custom CSS for glassmorphism and premium look
st.markdown(
    """
<style>
    .main {
        background-color: #0e1117;
    }
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161b22 100%);
    }
    .agent-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🤖 Multi-Agent Auditor System")
st.markdown("""
This system leverages a **Multi-Agent Architecture** to audit product listings. 
Different specialized agents analyze the photo and textual information (title, specs) 
sequentially before a Master Agent makes the final decision.
""")

# --- Session State & Loading Logic ---
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "loaded_session_id" not in st.session_state:
    st.session_state.loaded_session_id = None
if "input_defaults" not in st.session_state:
    st.session_state.input_defaults = {}

# Check for 'id' parameter to load session
try:
    query_params = st.query_params
    qp_id = query_params.get("id")
    if qp_id and qp_id != st.session_state.loaded_session_id:
        # Load the session
        try:
            resp = requests.get(f"{API_BASE_URL}/audit/session/{qp_id}")
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.loaded_session_id = qp_id
                st.session_state.audit_result = data["audit_result"]
                st.session_state.input_defaults = {
                    "product_title": data["product_title"],
                    "product_specs": data["product_specs"],
                    "mcat_name": data["mcat_name"],
                    "image_url": data.get("image_url")
                }
                st.success(f"Session {qp_id} loaded successfully.")
            else:
                st.error("Failed to load session details.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
except Exception as e:
    # Fallback for older streamlit versions if query_params fails
    print(f"Warning: {e}")


# --- Input Section ---
st.subheader("📥 Product Information")
with st.container(border=True):
    col1, col2 = st.columns([1, 2])

    defaults = st.session_state.input_defaults

    with col1:
        uploaded_file = st.file_uploader(
            "Upload Product Photo", type=["jpg", "jpeg", "png", "webp"]
        )
        
        # Logic to display image: Uploaded > Loaded 
        display_image = None
        if uploaded_file:
            display_image = uploaded_file
        elif defaults.get("image_url"):
            display_image = f"http://localhost:8000{defaults['image_url']}"
            
        if display_image:
            st.image(display_image, caption="Product Preview", use_container_width=True)

    with col2:
        product_title = st.text_input(
            "Product Title", 
            placeholder="Enter official product name...",
            value=defaults.get("product_title", "")
        )
        mcat_name = st.text_input(
            "Category Name", 
            placeholder="Enter product category...",
            value=defaults.get("mcat_name", "")
        )
        product_specs = st.text_area(
            "Product Specifications",
            placeholder="Enter key specs (e.g., Color: Red, Size: XL)...",
            height=200,
            value=defaults.get("product_specs", "")
        )
        submit_button = st.button(
            "🚀 Run Multi-Agent Audit", use_container_width=True, type="primary"
        )


def get_usage_str(agent_result):
    raw = agent_result.get("raw_output", {})
    if isinstance(raw, dict) and "usage" in raw and raw["usage"]:
        u = raw["usage"]
        return f"\n[In: {u.get('prompt_tokens', 0)} | Out: {u.get('completion_tokens', 0)}]"
    return ""

def display_audit_results(result, is_loaded_view=False):
    st.divider()
    
    total_time = result.get("total_processing_time", 0.0)
    total_cost = result.get("total_cost", 0.0)

    st.success(
        f"Audit Complete in {total_time:.2f}s | Total Cost: {format_inr(total_cost)}"
    )

    # Agents Visualization
    # Photo & Textual
    col_p, col_t = st.columns(2)
    with col_p:
        res = result["photo_agent"]
        st.info(
            f"Photo Agent: Done ({res['processing_time']:.1f}s | {format_inr(res.get('cost', 0))})"
            f"{get_usage_str(res)}"
        )
        with st.expander("View Photo Analysis"):
            st.json(res.get("raw_output", {}))

    with col_t:
        res = result["textual_agent"]
        st.info(
            f"Textual Agent: Done ({res['processing_time']:.1f}s | {format_inr(res.get('cost', 0))})"
            f"{get_usage_str(res)}"
        )
        with st.expander("View Textual Analysis"):
            st.json(res.get("raw_output", {}))
            
    # RCA Agent
    rca_res = result.get("rca_agent")
    if rca_res:
        st.info(
            f"RCA Agent: Done ({rca_res['processing_time']:.1f}s | {format_inr(rca_res.get('cost', 0))})"
            f"{get_usage_str(rca_res)}"
        )
        with st.expander("View RCA Raw Output"):
            st.json(rca_res.get("raw_output", {}))
    
    # Master Decision
    st.subheader("⚖️ Phase 3: Final Decision")
    with st.container():
        master_data = result["master_agent"]["raw_output"]
        decision = result["master_agent"]["audit_decision"]

        # RCA Details
        if rca_res and rca_res.get("analysis"):
            rca_analysis = rca_res["analysis"]
            st.markdown("### 🔍 Root Cause Analysis")
            st.info(
                f"**Summary:** {rca_analysis.get('root_cause_summary', 'N/A')}"
            )

            issues = rca_analysis.get("identified_issues", [])
            if issues:
                import pandas as pd
                df_issues = pd.DataFrame(issues)
                st.dataframe(
                    df_issues,
                    column_config={
                        "severity": st.column_config.TextColumn("Severity", width="small"),
                        "issue_type": st.column_config.TextColumn("Issue Type", width="medium"),
                        "description": st.column_config.TextColumn("Description", width="large"),
                        "evidence": st.column_config.TextColumn("Evidence", width="large"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )

        st.divider()
        col_res, col_score = st.columns(2)

        with col_res:
            d_code = result["master_agent"].get("decision_code", "N/A")
            if decision == "PASS":
                st.success(f"### FINAL DECISION: **{decision}**")
            elif decision == "FAIL":
                st.error(f"### FINAL DECISION: **{decision}**")
            else:
                st.warning(f"### FINAL DECISION: **{decision}**")

            # Show Master Agent Usage & Cost
            master_res = result["master_agent"]
            st.caption(
                f"Decision Rule Code: {d_code} | "
                f"Cost: {format_inr(master_res.get('cost', 0))} | "
                f"Time: {master_res.get('processing_time', 0):.1f}s"
                f"{get_usage_str(master_res)}"
            )

        with col_score:
            st.metric(
                "Confidence Score",
                f"{result['master_agent']['confidence_score']:.2%}",
            )

        st.markdown("#### 📝 Auditor Reasoning")
        for r in result["master_agent"].get("reasons", []):
            st.markdown(f"- {r}")

        recommendation = result["master_agent"].get("seller_recommendation")
        if recommendation:
            st.success(f"**💡 Seller Recommendation:** {recommendation}")

        st.markdown("#### 🔍 Optimized Search Query")
        search_query = result["master_agent"].get(
            "product_search_query"
        ) or master_data.get("product_search_query", "N/A")
        st.code(search_query)

        with st.expander("View Detailed Cross-Validation Matrix"):
            st.json(result["master_agent"].get("cross_validation", {}))
            st.json(result["master_agent"].get("final_errors", {}))


# --- Execution Section ---

if submit_button:
    if not uploaded_file or not product_title or not mcat_name or not product_specs:
        st.error(
            "Please provide all inputs (Photo, Title, Category Name, and Specs) to proceed."
        )
    else:
        # Clear previous result in state
        st.session_state.audit_result = None
        st.session_state.loaded_session_id = None # New run clears loaded context
        
        # Execution Phase Visualization
        st.subheader("🕵️ Phase 1: Base Analysis")
        flow_col1, flow_col2 = st.columns(2)
        with flow_col1:
            photo_card = st.empty()
            photo_card.info("🔄 Photo Agent: Running...")
        with flow_col2:
            textual_card = st.empty()
            textual_card.warning("⏳ Textual Agent: Waiting for Photo...")

        st.subheader("🔍 Phase 2: RCA Verification")
        rca_card = st.empty()
        rca_card.warning("⏳ RCA Agent: Waiting for Phase 1...")

        st.subheader("⚖️ Phase 3: Final Decision")
        master_placeholder = st.empty()
        master_placeholder.warning("⏳ Master Agent: Waiting for RCA...")

        # API Call
        try:
            # Prepare multipart form-data
            file_bytes = uploaded_file.getvalue()
            files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type)}
            data = {
                "product_title": product_title,
                "mcat_name": mcat_name,
                "product_specs": product_specs,
            }

            response = requests.post(
                f"{API_BASE_URL}/audit/multi-agent", data=data, files=files
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.audit_result = result
                st.session_state.uploaded_file_bytes = file_bytes # Cache for saving later
                st.session_state.uploaded_file_name = uploaded_file.name
                
                # We can't use 'display_audit_results' here directly because we wanted the progressive loading animation
                # But for simplicity, we let the animation finish (it was just placeholders) and then show static results
                # Actually, the user experience is better if we just re-render the whole page with results
                st.rerun()
                
            else:
                st.error(f"Audit failed: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"Connection Error: {e}")

# Display Results if available
if st.session_state.audit_result:
    display_audit_results(st.session_state.audit_result)
    
    st.divider()
    st.subheader("💾 Save & Share")
    
    # If loaded session, just show the link
    if st.session_state.loaded_session_id:
        share_url = f"{APP_BASE_URL}/Multi_Agent_Auditor?id={st.session_state.loaded_session_id}"
        st.success(f"**Shareable Link:** {share_url}")
        st.info("You are viewing a saved session.")
    
    # If fresh run, show save button
    else:
        # We need the file bytes. If we ran, we stored them.
        if "uploaded_file_bytes" in st.session_state:
            # We use a form to hold the input state or just a button. 
            # A simple button is fine, but we need to handle the state.
            
            if st.button("Save and Generate Link"):
                with st.spinner("Saving session..."):
                    try:
                        # Re-construct file for upload
                        files = {
                            "file": (
                                st.session_state.uploaded_file_name, 
                                st.session_state.uploaded_file_bytes, 
                                "image/jpeg" # Assumption/Fallback
                            )
                        }
                        
                        save_data = {
                            "product_title": product_title,
                            "product_specs": product_specs,
                            "mcat_name": mcat_name,
                            "audit_result": json.dumps(st.session_state.audit_result)
                        }
                        
                        save_resp = requests.post(
                            f"{API_BASE_URL}/audit/save",
                            data=save_data,
                            files=files
                        )
                        
                        if save_resp.status_code == 200:
                            new_id = save_resp.json()["session_id"]
                            st.session_state.loaded_session_id = new_id
                            st.success("Session saved!")
                            st.rerun()
                        else:
                            st.error(f"Save failed: {save_resp.text}")
                            
                    except Exception as e:
                        st.error(f"Error saving: {e}")

