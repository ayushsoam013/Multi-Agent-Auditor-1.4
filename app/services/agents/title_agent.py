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
            response_class=TitleAgentResponse
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        if not request.product_title:
            raise ValueError("TitleAgent requires a product_title")

        # Extract PhotoAgent result from context if available
        photo_res = request.context.get("photo_analysis", {})
        photo_data = {}
        if photo_res:
            # Handle both object (from orchestrator) and dict (if manual)
            if hasattr(photo_res, "task_1"):
                task1 = photo_res.task_1
                photo_data = {
                    "primary_object": task1.get("primary_object", ""),
                    "photo_description": task1.get("photo_description", ""),
                    "ocr_text": photo_res.task_2.get("ocr_text", []),
                    "photo_specifications": photo_res.task_3.get("photo_specifications", {})
                }
            else:
                task1 = photo_res.get("task_1", {})
                photo_data = {
                    "primary_object": task1.get("primary_object", ""),
                    "photo_description": task1.get("photo_description", ""),
                    "ocr_text": photo_res.get("task_2", {}).get("ocr_text", []),
                    "photo_specifications": photo_res.get("task_3", {}).get("photo_specifications", {})
                }

        prompt = f"""
Product Title: {request.product_title}
Product Specifications: {request.product_specs or "N/A"}
Category Name: {request.mcat_name or "N/A"}
Photo Agent Output (Textual Only):
{json.dumps(photo_data, indent=2)}

Instructions:

Task 1: 
 Product Title Assessment (Internal Only) : Evaluate the Product Title text in isolation: 
	a) Spell Error
b) Duplicate words in Product Title
c) Contradiction in Product Title 
(Conflict within the Title text itself)

  Task 2: 
 Product Specifications Assessment (Internal Only):  Evaluate the Product Specifications text in isolation: 
a) Spell Error 
b) Duplicate Specifications 
c) Internal Contradiction 
(Conflict within the Specifications text itself)

  Task 3:
 Identify well-known brands, models, or recognizable features from:
- Primary Object
- OCR text from Input
- Product Title
- Product Specifications
- Photo Specifications
 Give 1 line reason for why Popular for each entity identified as popular.

  Task 4:
    Query Construction: Combine the entities from Task 3  into a relevant search query. Let's call it a Product Search Query.

  Task 5: 
    Identify if there is contradiction in:
Analyze each pair independently. An "outlier" here requires a mismatch between the two listed sources. If the sources agree on the core fact, it is "not outlier," even if one source is poorly formatted or has internal errors.
      a) Primary Object of Product Photo- Title
      b) Primary Object of Product Photo - Product Specifications
      c) Product Title - Product Specifications 
      d) Within the Product Search Query
     e) Photo Description ↔ Product Title
     f) Photo Specifications ↔ Product Specifications

    Task 6:
Category Analysis: Analyze the Category : "Category Name"  and identify the type of products it represents.
Only flag as "outlier" if the entity does not belong in the category. Ignore spelling/formatting errors in the entities. Use the Category understanding from above to identify if there is a contradiction in:
      a) Primary Object ↔ Category
      b) Photo Description ↔ Category
      c) Product Search Query - Category Name
      d) Product title - Category Name


  Task 7:
Core Alignment Check : Verify if the product's primary function and operating mechanism match the category's fundamental definition. Flag as outlier if:
Mechanism Mismatch: The product operates differently than the category implies (e.g., manual vs. electric, stovetop vs. automatic).
Entity Mismatch: The product is a toy, model, accessory, or spare part, while the category represents the functional standalone item.
Visual Mimicry: The product is designed to look like the category item but lacks its core utility (e.g., a camera-shaped lighter).

Give all output in JSON format matching this schema:
{{
  "task_1": {{
    "spell_error": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "duplicate_words": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "internal_contradiction": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }},
  "task_2": {{
    "spell_error": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "duplicate_specifications": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "internal_contradiction": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }},
  "task_3": {{
    "identified_entities": [
      {{
        "entity": "",
        "source": "",
        "why_popular": ""
      }}
    ]
  }},
  "task_4": {{
    "product_search_query": ""
  }},
  "task_5": {{
    "photo_title": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "photo_specs": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "title_specs": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "query_internal": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "photo_description_title": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "photo_specs_specs": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }},
  "task_6": {{
    "primary_object_category": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "photo_description_category": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "query_category": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "title_category": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }},
  "task_7": {{
    "mechanism_mismatch": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "entity_mismatch": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }},
    "visual_mimicry": {{ "status": "outlier/not_outlier/can't_say", "reason": "" }}
  }}
}}
"""
        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": prompt}],
            config={"response_mime_type": "application/json"}
        )
        
        raw_text = response.get("content", "{}")
        try:
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"Failed to parse TitleAgent response: {raw_text}")
            raise e

    def _validate_input(self, request: AgentRequest):
        if not request.product_title:
            raise ValueError("TitleAgent requires a product_title.")
