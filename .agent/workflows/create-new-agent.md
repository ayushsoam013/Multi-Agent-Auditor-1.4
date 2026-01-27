---
description: Steps to create and register a new specialized agent in the Multi-Agent Auditor system.
---

This workflow guides you through the process of adding a new agent to the orchestration layer.

1. **Define Schema**
   - Open `app/schemas/agent_schemas.py`.
   - Create a specific `AnalysisResult` model for the agent's findings.
   - Create a `[Name]AgentResponse` model inheriting from `BaseAgentResponse`.
   - Add the new response type to `MultiAgentAuditResult`.

2. **Implement Agent Class**
   - Create `app/services/agents/[name]_agent.py`.
   - Inherit from `BaseAgent`.
   - Initialize with `super().__init__(agent_name="...", response_class=...)`.
   - Implement `_process_logic(self, request: AgentRequest)`.
   - Use `self.gen_service.chat_with_usage(...)` for LLM calls with JSON output.

3. **Register in Orchestrator**
   - Open `app/services/multi_agent_orchestrator.py`.
   - Import the new agent class.
   - Initialize it in `__init__`.
   - Add it to the execution flow in `run_audit` or wherever appropriate.

4. **Update Frontend (Optional)**
   - If the new agent output needs to be visualized, update `streamlit_app/` components to handle the new field in `MultiAgentAuditResult`.
