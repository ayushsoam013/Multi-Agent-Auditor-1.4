import json
import logging
from typing import Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import (
    AgentRequest,
    BackendReviewAgentResponse,
)

logger = logging.getLogger(__name__)


class BackendReviewAgent(BaseAgent):
    """
    Agent specialized in reviewing Backend (FastAPI, Pydantic, Python) code.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="BackendReviewAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=BackendReviewAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        context = request.context or {}
        backend_diff = context.get("backend_diff", "")

        if not backend_diff:
            return {
                "summary": "No backend changes detected.",
                "issues": [],
                "security_concerns": [],
                "performance_tips": [],
            }

        prompt = self._get_prompt(backend_diff)

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
            logger.error(f"Failed to parse BackendReviewAgent response: {raw_text}")
            # Return a fallback empty result on parse error to avoid crashing the whole chain
            return {
                "summary": "Failed to parse analysis result.",
                "issues": [],
                "security_concerns": [],
                "performance_tips": [],
                "_cost": response.get("costing", 0.0),
            }

    def _get_prompt(self, diff: str) -> str:
        return f"""
You are a Senior Backend Engineer expert in Python, FastAPI, Pydantic, and AsyncIO.
Review the following git diff for code quality, security, performance, and best practices.

GIT DIFF:
{diff}

Instructions:
1. Identify potential bugs, logic errors, or race conditions.
2. Check for security vulnerabilities (SQL injection, XSS, insecure dependencies, secret exposure).
3. Suggest performance improvements (async usage, database queries, caching).
4. Verify strict typing (Pydantic models, type hints).

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
  "security_concerns": ["concerns..."],
  "performance_tips": ["tips..."]
}}
"""
