import json
import logging
from typing import Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import AgentRequest, SpecsAgentResponse

logger = logging.getLogger(__name__)


class SpecsAgent(BaseAgent):
    """
    Specialized agent for auditing product specifications.
    Focuses on technical accuracy, formatting, and internal consistency.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="SpecsAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=SpecsAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Specs Logic:
        1. Perform spell check on technical terms.
        2. Detect redundant/duplicate specifications.
        3. Verify that specs do not contradict the product title.
        4. Structured extraction of key-value attributes for database ingestion.
        """
        if not request.product_specs:
            return {
                "spell_errors": [],
                "duplicate_specs": [],
                "contradictions": [],
                "extracted_specs": {},
            }

        prompt = f"""
Analyze the following product specifications:
"{request.product_specs}"

Cross-reference with Product Title if provided: "{request.product_title or "N/A"}"

Tasks:
1. Spell Check: Identify any spelling errors in the specs.
2. Duplicate Specs: Detect repeated or redundant specification entries.
3. Contradictions: Check for internal contradictions or contradictions with the title.
4. Spec Extraction: Extract key-value pairs of specifications.

Return the results in this strict JSON format:
{{
  "spell_errors": ["string"],
  "duplicate_specs": ["string"],
  "contradictions": ["string"],
  "extracted_specs": {{"key": "value"}}
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
            logger.error(f"Failed to parse SpecsAgent response: {raw_text}")
            raise e
