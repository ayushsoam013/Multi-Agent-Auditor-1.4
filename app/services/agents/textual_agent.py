import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import AgentRequest, TextualAgentResponse

logger = logging.getLogger(__name__)


class TextualAgent(BaseAgent):
    """
    Specialized agent for auditing product textual information (Title, Specs)
    and checking consistency with Photo and Category.
    Combines functionality of TitleAgent and SpecsAgent.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="TextualAgent",
            model_name=model_name or settings.GEMINI_GEN_MODEL,
            response_class=TextualAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Textual Analysis Logic.
        """
        # Extract Photo Agent Output from context if available
        photo_output_str = "{}"
        if request.context and "photo_agent" in request.context:
            photo_res = request.context["photo_agent"]

            photo_data = {
                "primary_object": "",
                "ocr_text": [],
                "photo_specifications": {},
            }

            # Helper to safely get attributes from object or dict
            def get_attr(obj, attr, default=None):
                if isinstance(obj, dict):
                    return obj.get(attr, default)
                return getattr(obj, attr, default)

            analysis = get_attr(photo_res, "analysis")
            if analysis:
                task_1 = get_attr(analysis, "task_1")  # Primary Object
                if task_1:
                    photo_data["primary_object"] = get_attr(
                        task_1, "primary_object", ""
                    )

                task_2 = get_attr(analysis, "task_2")  # OCR
                if task_2:
                    photo_data["ocr_text"] = get_attr(task_2, "ocr_text", [])

                task_3 = get_attr(analysis, "task_3")  # Photo Specs
                if task_3:
                    photo_data["photo_specifications"] = get_attr(
                        task_3, "photo_specifications", {}
                    )

            photo_output_str = json.dumps(photo_data, indent=2)

        prompt = f"""
Product Title: {request.product_title or "N/A"}
Product Specifications: {request.product_specs or "N/A"}
Category Name: {request.mcat_name or "N/A"}
Photo Agent Output (Textual Only):
{photo_output_str}


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
      e) Photo Specifications ↔ Product Specifications

    Task 6:
Category Analysis: Analyze the Category : "Category Name"  and identify the type of products it represents.
Only flag as "outlier" if the entity does not belong in the category. Ignore spelling/formatting errors in the entities. Use the Category understanding from above to identify if there is a contradiction in:
      a) Primary Object ↔ Category
      b) Product Search Query - Category Name
      c) Product title - Category Name


  Task 7:
Core Alignment Check : Verify if the product's primary function and operating mechanism match the category's fundamental definition. Flag as outlier if:
Mechanism Mismatch: The product operates differently than the category implies (e.g., manual vs. electric, stovetop vs. automatic).
Entity Mismatch: The product is a toy, model, accessory, or spare part, while the category represents the functional standalone item.
Visual Mimicry: The product is designed to look like the category item but lacks its core utility (e.g., a camera-shaped lighter).
Give all output in JSON format.
Give response for task and subtasks of task 1,  task 2, task 5, task 6 and task 7 as outlier / not outlier / can't say for each subtask. Give one reason for each subtask of task 1,  task 2, task 5, task 6 and task 7.


{{
  "task_1": {{
    "spell_error": {{ "status": "", "reason": "" }},
    "duplicate_words": {{ "status": "", "reason": "" }},
    "internal_contradiction": {{ "status": "", "reason": "" }}
  }},
  "task_2": {{
    "spell_error": {{ "status": "", "reason": "" }},
    "duplicate_specifications": {{ "status": "", "reason": "" }},
    "internal_contradiction": {{ "status": "", "reason": "" }}
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
    "photo_title": {{ "status": "", "reason": "" }},
    "photo_specs": {{ "status": "", "reason": "" }},
    "title_specs": {{ "status": "", "reason": "" }},
    "query_internal": {{ "status": "", "reason": "" }},
    "photo_specs_specs": {{ "status": "", "reason": "" }}
  }},
  "task_6": {{
    "primary_object_category": {{ "status": "", "reason": "" }},
    "query_category": {{ "status": "", "reason": "" }},
    "title_category": {{ "status": "", "reason": "" }}
  }},
  "task_7": {{
    "mechanism_mismatch": {{ "status": "", "reason": "" }},
    "entity_mismatch": {{ "status": "", "reason": "" }},
    "visual_mimicry": {{ "status": "", "reason": "" }}
  }}
}}
"""
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
            logger.error(f"Failed to parse TextualAgent response: {raw_text}")
            raise e
