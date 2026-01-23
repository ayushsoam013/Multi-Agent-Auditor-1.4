import json
import logging
from typing import Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import (
    AgentRequest,
    StreamlitReviewAgentResponse,
)

logger = logging.getLogger(__name__)


class StreamlitReviewAgent(BaseAgent):
    """
    Agent specialized in reviewing Streamlit Frontend code.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="StreamlitReviewAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=StreamlitReviewAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        context = request.context or {}
        streamlit_diff = context.get("streamlit_diff", "")

        if not streamlit_diff:
            return {
                "summary": "No streamlit changes detected.",
                "issues": [],
                "ux_improvements": [],
                "state_management_issues": [],
            }

        prompt = self._get_prompt(streamlit_diff)

        # Call LLM
        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": prompt}],
            config={"response_mime_type": "application/json"},
        )

        raw_text = response.get("content", "{}")
        try:
            if raw_text.startswith("```json"):
                raw_text = raw_text.strip("```json").strip("```").strip()

            analysis_dict = json.loads(raw_text)
            analysis_dict["_cost"] = response.get("costing", 0.0)
            return analysis_dict
        except Exception as e:
            logger.error(f"Failed to parse StreamlitReviewAgent response: {raw_text}")
            return {
                "summary": "Failed to parse analysis result.",
                "issues": [],
                "ux_improvements": [],
                "state_management_issues": [],
                "_cost": response.get("costing", 0.0),
            }

    def _get_prompt(self, diff: str) -> str:
        return f"""
You are a Senior Frontend Engineer expert in Streamlit and Python.
Review the following git diff for UX/UI best practices, Session State management, and performance.

GIT DIFF:
{diff}

Instructions:
1. Check for correct usage of `st.session_state` to persist data.
2. Identify unnecessary re-runs or performance bottlenecks (e.g., heavy computations outside @st.cache_data).
3. Review UI layout and user experience (clarity, responsiveness).
4. Ensure error handling is user-friendly (st.error, st.warning).

Return the results in this strict JSON format:
{{
  "summary": "Brief summary of the changes and overall quality",
  "issues": [
    {{
      "file": "filename",
      "line": 123,
      "severity": "info/warning/critical",
      "message": "Description of the issue",
      "suggestion": "How to fix it"
    }}
  ],
  "ux_improvements": ["suggestions..."],
  "state_management_issues": ["issues..."]
}}
"""
