import streamlit as st
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Multi-Agent Auditor", page_icon="🤖", layout="wide")

# Custom CSS for glassmorphism and premium look
st.markdown("""
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
""", unsafe_allow_html=True)

st.title("🤖 Multi-Agent Auditor System")
st.markdown("""
This system leverages a **Multi-Agent Architecture** to audit product listings. 
Different specialized agents analyze the photo, title, and specifications in parallel 
before a Master Agent makes the final decision.
""")

# --- Input Section ---
with st.container():
    st.subheader("📥 Product Information")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Product Photo", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Product Preview", use_container_width=True)
            
    with col2:
        product_title = st.text_input("Product Title", placeholder="Enter official product name...")
        product_specs = st.text_area("Product Specifications", placeholder="Enter key specs (e.g., Color: Red, Size: XL)...", height=200)

    submit_button = st.button("🚀 Run Multi-Agent Audit", use_container_width=True, type="primary")

# --- Execution Section ---
if submit_button:
    if not uploaded_file or not product_title or not product_specs:
        st.error("Please provide all inputs (Photo, Title, and Specs) to proceed.")
    else:
        # Progress states
        st.divider()
        st.subheader("⚡ Processing Flow")
        
        # We start by showing the parallel agent columns
        flow_col1, flow_col2, flow_col3 = st.columns(3)
        
        with flow_col1:
            photo_status = st.empty()
            photo_status.info("Photo Agent: Waiting...")
            
        with flow_col2:
            title_status = st.empty()
            title_status.info("Title Agent: Waiting...")
            
        with flow_col3:
            specs_status = st.empty()
            specs_status.info("Specs Agent: Waiting...")
            
        master_status = st.status("Master Agent: Coordinating...", expanded=True)
        
        # API Call
        try:
            # Prepare multipart form-data
            # Re-read file content as bytes
            file_bytes = uploaded_file.getvalue()
            files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type)}
            data = {
                "product_title": product_title,
                "product_specs": product_specs
            }
            
            # Start timer
            start_time = time.time()
            
            # Update UI to "Processing"
            photo_status.warning("Photo Agent: Running...")
            title_status.warning("Title Agent: Running...")
            specs_status.warning("Specs Agent: Running...")
            
            # Simulating a slight delay for flow visualization if it's too fast
            # time.sleep(1) 

            response = requests.post(f"{API_BASE_URL}/audit/multi-agent", data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                total_time = result.get("total_processing_time", 0.0)
                
                # Update Statuses
                photo_status.success(f"Photo Agent: Done ({result['photo_agent']['processing_time']:.1f}s)")
                title_status.success(f"Title Agent: Done ({result['title_agent']['processing_time']:.1f}s)")
                specs_status.success(f"Specs Agent: Done ({result['specs_agent']['processing_time']:.1f}s)")
                
                # Show Agent Details
                with flow_col1:
                    with st.expander("View Photo Analysis"):
                        st.json(result['photo_agent'].get('raw_output', {}))
                
                with flow_col2:
                    with st.expander("View Title Analysis"):
                        st.json(result['title_agent'].get('raw_output', {}))
                    
                with flow_col3:
                    with st.expander("View Specs Analysis"):
                        st.json(result['specs_agent'].get('raw_output', {}))
                
                # Master Agent Result
                master_status.update(label=f"Master Agent: Audit Complete in {total_time:.2f}s", state="complete", expanded=True)
                
                with master_status:
                    master_data = result['master_agent']['raw_output']
                    decision = result['master_agent']['audit_decision']
                    
                    st.markdown("---")
                    col_res, col_score = st.columns(2)
                    
                    with col_res:
                        if decision == "PASS":
                            st.success(f"### FINAL DECISION: **{decision}**")
                        elif decision == "FAIL":
                            st.error(f"### FINAL DECISION: **{decision}**")
                        else:
                            st.warning(f"### FINAL DECISION: **{decision}**")
                            
                    with col_score:
                        st.metric("Confidence Score", f"{result['master_agent']['confidence_score']:.2%}")
                    
                    st.markdown("#### 📝 Auditor Reasoning")
                    for r in master_data.get('reasons', []):
                        st.markdown(f"- {r}")
                        
                    st.markdown("#### 🔍 Optimized Search Query")
                    st.code(master_data.get('product_search_query', 'N/A'))
                    
                    with st.expander("View Detailed Cross-Validation Matrix"):
                        st.json(result['master_agent'].get('cross_validation', {}))
                        st.json(master_data.get('final_errors', {}))
            else:
                st.error(f"Audit failed: {response.status_code} - {response.text}")
                master_status.update(label="Master Agent: Error", state="error")
                
        except Exception as e:
            st.error(f"Connection Error: {e}")
            master_status.update(label="Master Agent: Connection Failed", state="error")
