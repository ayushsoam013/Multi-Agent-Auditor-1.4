import asyncio
import logging
import subprocess
import time
from typing import Dict, Any, Optional, cast
from app.services.agents.base_agent import BaseAgent
from app.services.agents.backend_review_agent import BackendReviewAgent
from app.services.agents.streamlit_review_agent import StreamlitReviewAgent
from app.schemas.agent_schemas import (
    AgentRequest,
    CodeReviewAgentResponse,
    BackendReviewAgentResponse,
    StreamlitReviewAgentResponse,
    CodeReviewAnalysisResult,
)

logger = logging.getLogger(__name__)


class CodeReviewAgent(BaseAgent):
    """
    Orchestrator agent for Code Reviews.
    Analyzes git diffs and delegates to specialized sub-agents.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="CodeReviewAgent",
            model_name=model_name or "gemini-1.5-flash",
            response_class=CodeReviewAgentResponse,
        )
        self.backend_agent = BackendReviewAgent(model_name=model_name)
        self.streamlit_agent = StreamlitReviewAgent(model_name=model_name)

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        # Ensure context exists
        if request.context is None:
            request.context = {}

        # 1. Get Git Diff
        full_diff = request.context.get("git_diff")
        if not full_diff:
            full_diff = self._get_git_diff()
            if not full_diff:
                return {
                    "summary": "No changes detected in git.",
                    "general_recommendations": [
                        "Make some changes before requesting a review."
                    ],
                }

        # 2. Split Diff
        backend_diff, streamlit_diff = self._split_diff(full_diff)

        request.context["backend_diff"] = backend_diff
        request.context["streamlit_diff"] = streamlit_diff

        # 3. Run Sub-Agents in Parallel
        backend_task = self.backend_agent.process(request)
        streamlit_task = self.streamlit_agent.process(request)

        results = await asyncio.gather(backend_task, streamlit_task)

        backend_res = cast(BackendReviewAgentResponse, results[0])
        streamlit_res = cast(StreamlitReviewAgentResponse, results[1])

        # 4. Aggregate Results
        total_cost = (backend_res.cost or 0.0) + (streamlit_res.cost or 0.0)

        # Construct the final analysis result
        # Note: We need to extract the 'analysis' part from the sub-agent responses

        backend_analysis = backend_res.analysis
        streamlit_analysis = streamlit_res.analysis

        summary_parts = []
        if backend_diff:
            summary_parts.append(
                f"Backend: {len(backend_analysis.issues) if backend_analysis else 0} issues."
            )
        if streamlit_diff:
            summary_parts.append(
                f"Frontend: {len(streamlit_analysis.issues) if streamlit_analysis else 0} issues."
            )

        summary = "Code Review Complete. " + " ".join(summary_parts)

        return {
            "summary": summary,
            "backend_review": backend_analysis.model_dump()
            if backend_analysis
            else None,
            "streamlit_review": streamlit_analysis.model_dump()
            if streamlit_analysis
            else None,
            "general_recommendations": [],  # Could add a synthesis step here if needed
            "_cost": total_cost,
        }

    def _get_git_diff(self) -> str:
        """
        Fetches the current git diff (staged and unstaged)
        """
        try:
            # Diff for unstaged changes
            unstaged = subprocess.check_output(["git", "diff"], text=True)
            # Diff for staged changes
            staged = subprocess.check_output(["git", "diff", "--staged"], text=True)
            return staged + "\n" + unstaged
        except Exception as e:
            logger.error(f"Failed to get git diff: {e}")
            return ""

    def _split_diff(self, diff: str) -> tuple[str, str]:
        """
        Splits the diff into Backend (app/) and Streamlit (streamlit_app/) parts.
        This is a naive implementation based on file paths in the diff header.
        """
        backend_lines = []
        streamlit_lines = []

        current_section = None  # 'backend', 'streamlit', or 'other'

        lines = diff.split("\n")
        for line in lines:
            if line.startswith("diff --git"):
                # specific check for file paths
                # diff --git a/app/foo.py b/app/foo.py
                if "a/streamlit_app/" in line or "b/streamlit_app/" in line:
                    current_section = "streamlit"
                elif "a/app/" in line or "b/app/" in line or "requirements.txt" in line:
                    current_section = "backend"
                else:
                    current_section = "other"  # Maybe treat as backend or ignore?

            if current_section == "backend":
                backend_lines.append(line)
            elif current_section == "streamlit":
                streamlit_lines.append(line)

        return "\n".join(backend_lines), "\n".join(streamlit_lines)
