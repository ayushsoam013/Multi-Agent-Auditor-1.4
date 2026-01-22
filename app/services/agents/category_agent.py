import json
import logging
from typing import Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import AgentRequest, CategoryAgentResponse

logger = logging.getLogger(__name__)


class CategoryAgent(BaseAgent):
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="CategoryAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=CategoryAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        prompt = self._get_category_prompt(request)

        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": prompt}],
            config={"response_mime_type": "application/json"},
        )

        raw_text = response.get("content", "{}")
        try:
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"Failed to parse CategoryAgent response: {raw_text}")
            raise e

    def _get_category_prompt(self, request: AgentRequest) -> str:
        context = request.context or {}
        photo_res = context.get("photo_agent")

        photo_context = ""
        if photo_res and photo_res.analysis:
            # Task 1: Visual Object & Description
            t1 = photo_res.analysis.task_1
            # Task 2: OCR
            t2 = photo_res.analysis.task_2

            ocr_text = (
                ", ".join(t2.get("ocr_text", [])) if t2.get("ocr_text") else "None"
            )

            photo_context = f"""
Photo Analysis:
- Visual Object: {t1.get("primary_object", "N/A")}
- Visual Description: {t1.get("photo_description", "N/A")}
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
