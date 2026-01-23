import json
import logging
from typing import Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import AgentRequest, RCAAgentResponse

logger = logging.getLogger(__name__)


class RCAAgent(BaseAgent):
    """
    The RCA (Root Cause Analysis) Agent is the synthesizer of the pipeline.
    It takes raw outputs from all specialized agents and performs a cross-modal
    analysis to find contradictions and deep-seated quality issues.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="RCAAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=RCAAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        RCA Logic:
        1. Consolidate results from Photo, Title, Specs, and Category agents.
        2. Identify core contradictions (e.g., photo shows a 'Chair' but title says 'Table').
        3. Assign severity levels and recommended verdicts for the Master Agent to process.
        """
        context = request.context or {}
        agent_results = context.get("agent_results", {})

        # Prepare context for RCA
        context_str = json.dumps(
            agent_results,
            indent=2,
            default=lambda o: o.dict() if hasattr(o, "dict") else str(o),
        )

        prompt = f"""
You are a Root Cause Analysis (RCA) specialist for product auditing.
Below are the results from various specialized agents that audited a product.

Agent Results:
{context_str}

Instructions:
1. Synthesize all findings.
2. Identify the root cause for any issues (outliers, contradictions, errors).
3. Determine the severity of each issue.
4. Recommend a final verdict (PASS, FAIL, REVIEW).
5. Provide a summary of your analysis.

Return the results in this strict JSON format:
{{
  "root_cause_summary": "string",
  "identified_issues": [
    {{
      "issue_type": "PHOTO_QUALITY | TITLE_QUALITY | SPECS_QUALITY | TITLE_SPECS_CONTRADICTION | PHOTO_TITLE_CONTRADICTION | PHOTO_SPECS_CONTRADICTION | PHOTO_CATEGORY_MISMATCH | TITLE_CATEGORY_MISMATCH | CATEGORY_MISMATCH | OTHER",
      "severity": "LOW/MEDIUM/HIGH/CRITICAL",
      "description": "string",
      "evidence": "string"
    }}
  ],
  "recommended_verdict": "PASS/FAIL/REVIEW",
  "confidence": float (0.0 to 1.0)
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
            logger.error(f"Failed to parse RCAAgent response: {raw_text}")
            raise e
