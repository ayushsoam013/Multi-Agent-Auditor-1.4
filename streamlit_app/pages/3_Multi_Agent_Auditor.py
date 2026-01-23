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

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
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
Different specialized agents analyze the photo, title, and specifications in parallel 
before a Master Agent makes the final decision.
""")

# --- Input Section ---
st.subheader("📥 Product Information")
with st.container(border=True):
    col1, col2 = st.columns([1, 2])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload Product Photo", type=["jpg", "jpeg", "png", "webp"]
        )
        if uploaded_file:
            st.image(uploaded_file, caption="Product Preview", use_container_width=True)

    with col2:
        product_title = st.text_input(
            "Product Title", placeholder="Enter official product name..."
        )
        product_specs = st.text_area(
            "Product Specifications",
            placeholder="Enter key specs (e.g., Color: Red, Size: XL)...",
            height=200,
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


# --- Execution Section ---
if submit_button:
    if not uploaded_file or not product_title or not product_specs:
        st.error("Please provide all inputs (Photo, Title, and Specs) to proceed.")
    else:
        # Execution Phase Visualization
        # Phase 1: Parallel Base Analysis (Independent Agents)
        st.subheader("🕵️ Phase 1: Parallel Base Analysis")
        flow_col1, flow_col2, flow_col3 = st.columns(3)
        with flow_col1:
            photo_card = st.empty()
            photo_card.info("🔄 Photo Agent: Running...")
        with flow_col2:
            title_card = st.empty()
            title_card.info("🔄 Title Agent: Running...")
        with flow_col3:
            specs_card = st.empty()
            specs_card.info("🔄 Specs Agent: Running...")

        # Phase 2: Category & RCA (Dependent on Phase 1 results)
        st.subheader("🔍 Phase 2: Category & RCA Verification")
        cat_rca_col1, cat_rca_col2 = st.columns(2)
        with cat_rca_col1:
            cat_card = st.empty()
            cat_card.warning("⏳ Category Agent: Waiting for Phase 1...")
        with cat_rca_col2:
            rca_card = st.empty()
            rca_card.warning("⏳ RCA Agent: Waiting for Phase 2...")

        # Phase 3: Master Decision (Final synthesis and decision grid lookup)
        st.subheader("⚖️ Phase 3: Final Decision")
        master_placeholder = st.empty()
        master_placeholder.warning("⏳ Master Agent: Waiting for RCA...")

        # API Call
        try:
            # Prepare multipart form-data
            file_bytes = uploaded_file.getvalue()
            files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type)}
            data = {"product_title": product_title, "product_specs": product_specs}

            response = requests.post(
                f"{API_BASE_URL}/audit/multi-agent", data=data, files=files
            )

            if response.status_code == 200:
                result = response.json()
                total_time = result.get("total_processing_time", 0.0)
                total_cost = result.get("total_cost", 0.0)

                st.success(
                    f"Audit Complete in {total_time:.2f}s | Total Cost: {format_inr(total_cost)}"
                )

                # Update Placeholders with Results
                with photo_card.container():
                    res = result["photo_agent"]
                    st.info(
                        f"Photo Agent: Done ({res['processing_time']:.1f}s | {format_inr(res.get('cost', 0))})"
                        f"{get_usage_str(res)}"
                    )
                    with st.expander("View Photo Analysis"):
                        st.json(res.get("raw_output", {}))

                with title_card.container():
                    res = result["title_agent"]
                    st.info(
                        f"Title Agent: Done ({res['processing_time']:.1f}s | {format_inr(res.get('cost', 0))})"
                        f"{get_usage_str(res)}"
                    )
                    with st.expander("View Title Analysis"):
                        st.json(res.get("raw_output", {}))

                with specs_card.container():
                    res = result["specs_agent"]
                    st.info(
                        f"Specs Agent: Done ({res['processing_time']:.1f}s | {format_inr(res.get('cost', 0))})"
                        f"{get_usage_str(res)}"
                    )
                    with st.expander("View Specs Analysis"):
                        st.json(res.get("raw_output", {}))

                with cat_card.container():
                    cat_res = result.get("category_agent")
                    if cat_res:
                        st.info(
                            f"Category Agent: Done ({cat_res['processing_time']:.1f}s | {format_inr(cat_res.get('cost', 0))})"
                            f"{get_usage_str(cat_res)}"
                        )
                        with st.expander("View Category Analysis"):
                            st.json(cat_res.get("raw_output", {}))
                    else:
                        st.info("Category Agent: Skipped")

                with rca_card.container():
                    rca_res = result.get("rca_agent")
                    if rca_res:
                        st.info(
                            f"RCA Agent: Done ({rca_res['processing_time']:.1f}s | {format_inr(rca_res.get('cost', 0))})"
                            f"{get_usage_str(rca_res)}"
                        )
                        with st.expander("View RCA Raw Output"):
                            st.json(rca_res.get("raw_output", {}))
                    else:
                        st.info("RCA Agent: Skipped")

                # Master Agent Result Section
                master_placeholder.empty()
                with master_placeholder.container():
                    master_data = result["master_agent"]["raw_output"]
                    decision = result["master_agent"]["audit_decision"]

                    # RCA Section if available
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
                            # Use st.dataframe with column_config for better visibility and control
                            st.dataframe(
                                df_issues,
                                column_config={
                                    "severity": st.column_config.TextColumn(
                                        "Severity", width="small"
                                    ),
                                    "issue_type": st.column_config.TextColumn(
                                        "Issue Type", width="medium"
                                    ),
                                    "description": st.column_config.TextColumn(
                                        "Description", width="large"
                                    ),
                                    "evidence": st.column_config.TextColumn(
                                        "Evidence", width="large"
                                    ),
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

            else:
                st.error(f"Audit failed: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"Connection Error: {e}")
