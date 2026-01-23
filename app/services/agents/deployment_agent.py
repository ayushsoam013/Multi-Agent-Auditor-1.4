import os
import glob
from typing import Dict, Any, List
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import DeploymentAgentResponse, AgentRequest


class DeploymentAgent(BaseAgent):
    """
    Agent specialized in verifying deployment readiness for Render.
    Checks for configuration files, hardcoded URLs, and script robustness.
    """

    def __init__(self):
        super().__init__(
            agent_name="DeploymentAgent",
            model_name="rules-based",  # This agent uses deterministic logic
            response_class=DeploymentAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Performs the deployment readiness audit.
        """
        checks = []
        recommendations = []

        # 1. Check for render.yaml
        has_render = os.path.exists("render.yaml")
        checks.append(
            {
                "check_name": "Render Blueprint (render.yaml)",
                "status": "PASS" if has_render else "FAIL",
                "details": "Found render.yaml" if has_render else "Missing render.yaml",
            }
        )
        if not has_render:
            recommendations.append(
                "Create render.yaml to define the Render Web Service."
            )

        # 2. Check start.sh robustness
        start_sh_path = "start.sh"
        if os.path.exists(start_sh_path):
            with open(start_sh_path, "r") as f:
                content = f.read()
                if "nc -z" in content or "wait-for-it" in content or "curl" in content:
                    checks.append(
                        {
                            "check_name": "Start Script Robustness",
                            "status": "PASS",
                            "details": "start.sh uses a port check loop.",
                        }
                    )
                elif "sleep" in content:
                    checks.append(
                        {
                            "check_name": "Start Script Robustness",
                            "status": "FAIL",
                            "details": "start.sh uses simple 'sleep'. Use a port check loop instead.",
                        }
                    )
                    recommendations.append(
                        "Update start.sh to wait for localhost:8000 using netcat or curl."
                    )
                else:
                    checks.append(
                        {
                            "check_name": "Start Script Robustness",
                            "status": "FAIL",
                            "details": "start.sh might be missing wait logic.",
                        }
                    )
        else:
            checks.append(
                {
                    "check_name": "Start Script Existence",
                    "status": "FAIL",
                    "details": "Missing start.sh",
                }
            )

        # 3. Check for DEPLOY.md
        has_deploy_doc = os.path.exists("DEPLOY.md")
        checks.append(
            {
                "check_name": "Deployment Documentation",
                "status": "PASS" if has_deploy_doc else "FAIL",
                "details": "Found DEPLOY.md" if has_deploy_doc else "Missing DEPLOY.md",
            }
        )
        if not has_deploy_doc:
            recommendations.append(
                "Create DEPLOY.md with environment variable instructions."
            )

        # 4. Check for Hardcoded Localhost URLs in Streamlit
        # We look for "localhost:8000" in streamlit_app/
        hardcoded_files = []
        streamlit_dir = "streamlit_app"
        for root, _, files in os.walk(streamlit_dir):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Simple check: if "localhost:8000" is in the file AND it's not the default value in os.getenv
                        # We try to be smart. "http://localhost:8000" literal is bad.
                        # os.getenv("...", "http://localhost:8000") is OK (fallback).

                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if (
                                '"http://localhost:8000' in line
                                or "'http://localhost:8000" in line
                            ):
                                # Check if it is inside os.getenv
                                if "os.getenv" not in line and "API_BASE_URL =" in line:
                                    hardcoded_files.append(f"{path} (Line {i + 1})")
                                elif "requests." in line and "localhost:8000" in line:
                                    hardcoded_files.append(f"{path} (Line {i + 1})")

        if hardcoded_files:
            checks.append(
                {
                    "check_name": "Hardcoded URLs",
                    "status": "FAIL",
                    "details": f"Found hardcoded localhost:8000 in: {', '.join(hardcoded_files)}",
                }
            )
            recommendations.append(
                "Refactor hardcoded URLs to use API_BASE_URL env var."
            )
        else:
            checks.append(
                {
                    "check_name": "Hardcoded URLs",
                    "status": "PASS",
                    "details": "No hardcoded localhost URLs found.",
                }
            )

        # Determine Overall Status
        failed_checks = [c for c in checks if c["status"] == "FAIL"]
        overall_status = "NOT_READY" if failed_checks else "READY"

        return {
            "checks": checks,
            "overall_status": overall_status,
            "recommendations": recommendations,
        }
