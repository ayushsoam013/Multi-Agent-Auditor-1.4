import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.multi_agent_orchestrator import orchestrator
from app.schemas.agent_schemas import AgentRequest

async def main():
    image_path = os.path.abspath("misc/sofa.jpg")
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    request = AgentRequest(
        product_title="Modern 3-Seater Sofa",
        product_specs="Color: Grey, Material: Leather, Dimensions: 200x90x85cm",
        mcat_name="Sofas",
        image_path=image_path
    )

    print("Starting audit...")
    try:
        result = await orchestrator.run_audit(request)
        print("Audit complete!")
        print(f"Audit ID: {result.audit_id}")
        print(f"Total Time: {result.total_processing_time:.2f}s")
        print(f"Total Cost: ${result.total_cost:.4f}")
        print(f"Final Decision: {result.master_agent.audit_decision}")
        print(f"Decision Code: {result.master_agent.decision_code}")
        print(f"Seller Recommendation: {result.master_agent.seller_recommendation}")
    except Exception as e:
        print(f"Error during audit: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
