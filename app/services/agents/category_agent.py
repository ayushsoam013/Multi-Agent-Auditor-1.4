import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import AgentRequest, CategoryAgentResponse

logger = logging.getLogger(__name__)


class CategoryAgent(BaseAgent):
    """
    Specialized agent for category verification (MCAT alignment).
    Uses both text and visual descriptions to ensure the product is in the right aisle.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="CategoryAgent",
            model_name=model_name or settings.GEMINI_GEN_MODEL,
            response_class=CategoryAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Category Logic:
        - Cross-references Title/Specs with the "Photo Context" provided by the Photo Agent.
        - Validates if the current category is optimal or suggests a better alternative.
        """
        prompt = self._get_category_prompt(request)

        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": prompt}],
            config={"response_mime_type": "application/json"},
        )

        raw_text = response.get("content", "{}")
        try:
            analysis_dict = json.loads(raw_text)
            analysis_dict["_cost"] = response.get("costing", 0.0)
            return analysis_dict
        except Exception as e:
            logger.error(f"Failed to parse CategoryAgent response: {raw_text}")
            raise e

    def _get_category_prompt(self, request: AgentRequest) -> str:
        context = request.context or {}
        photo_res = context.get("photo_agent")

        photo_context = ""
        if photo_res and photo_res.analysis:
            # Task 1: Visual Object
            t1 = photo_res.analysis.task_1
            # Task 2: OCR
            t2 = photo_res.analysis.task_2

            ocr_text = (
                ", ".join(t2.get("ocr_text", [])) if t2.get("ocr_text") else "None"
            )

            # Safely get primary_object from PhotoTask1 model
            primary_obj = getattr(t1, "primary_object", "N/A")

            photo_context = f"""
Photo Analysis:
- Visual Object: {primary_obj}
- Detected Text (OCR): {ocr_text}
"""

        return f"""
Product Title: {request.product_title or "N/A"}
Product Specifications: {request.product_specs or "N/A"}
Current Category (if any): {request.mcat_name or "N/A"}
{photo_context}

Instructions:
1. Analyze the product information provided.
2. Determine the most accurate category for this product.
3. If the current category is correct, confirm it.
4. If there is a better category, suggest it.
5. Provide reasoning for your choice.

Return the results in this strict JSON format:
{{
  "suggested_category": "string",
  "confidence_score": float (0.0 to 1.0),
  "reasoning": "string",
  "alternative_categories": ["string"]
}}
"""
