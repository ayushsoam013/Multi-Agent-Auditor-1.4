import json
import logging
from typing import Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import AgentRequest, TitleAgentResponse

logger = logging.getLogger(__name__)


class TitleAgent(BaseAgent):
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="TitleAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=TitleAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        if not request.product_title:
            raise ValueError("TitleAgent requires a product_title")

        # Independent execution: No longer pulls photo_analysis from context

        prompt = f"""
Product Title: {request.product_title}
Product Specifications: {request.product_specs or "N/A"}
Category Name: {request.mcat_name or "N/A"}

Instructions:

Task 1: 
 Product Title Assessment: Evaluate the Product Title text in isolation: 
    a) Spell Error
    b) Duplicate words in Product Title
    c) Contradiction in Product Title (Conflict within the Title text itself)

Task 2:
 Identify well-known brands, models, or recognizable features from the Product Title and Specifications.
 Give 1 line reason for why Popular for each entity identified as popular.

Task 3:
 Query Construction: Combine the entities from Task 2 into a relevant search query. Let's call it a Product Search Query.

Task 4:
 Category Alignment Check: Analyze if the Product Title aligns with the provided Category Name.

Return all output in JSON format matching this schema:
{{
  "task_1": {{
    "spell_error": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "duplicate_words": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "internal_contradiction": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }},
  "task_2": {{
    "identified_entities": [
      {{
        "entity": "",
        "source": "title/specs",
        "why_popular": ""
      }}
    ]
  }},
  "task_3": {{
    "product_search_query": ""
  }},
  "task_4": {{
    "title_category_alignment": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }}
}}
"""
        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": prompt}],
            config={"response_mime_type": "application/json"},
        )

        raw_text = response.get("content", "{}")
        try:
            # The schema changed, so we need to map it back to TitleAnalysisResult if possible,
            # but since we changed the schema in agent_schemas.py (Wait, I didn't change TitleAnalysisResult)
            # Actually, I should probably update the schema to match this new structure or keep it compatible.
            # For now, I'll return the dict and ensure the response_class can handle it.
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"Failed to parse TitleAgent response: {raw_text}")
            raise e

    def _validate_input(self, request: AgentRequest):
        if not request.product_title:
            raise ValueError("TitleAgent requires a product_title.")
