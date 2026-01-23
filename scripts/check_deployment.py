import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.agents.deployment_agent import DeploymentAgent
from app.schemas.agent_schemas import AgentRequest


async def main():
    print("[*] Running Deployment Readiness Agent...")
    agent = DeploymentAgent()
    request = AgentRequest()  # No specific input needed for this agent

    response = await agent.process(request)

    if response.status == "failure":
        print(f"[!] Agent failed: {response.error_message}")
        return

    analysis = response.analysis
    print(f"\nOverall Status: {analysis.overall_status}")
    print("\nChecks:")
    for check in analysis.checks:
        icon = "[PASS]" if check.status == "PASS" else "[FAIL]"
        print(f"   {icon} {check.check_name}: {check.details}")

    if analysis.recommendations:
        print("\nRecommendations:")
        for rec in analysis.recommendations:
            print(f"   - {rec}")

    if analysis.overall_status == "READY":
        print("\nApplication is ready for deployment!")
        sys.exit(0)
    else:
        print("\nPlease fix the issues above before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
