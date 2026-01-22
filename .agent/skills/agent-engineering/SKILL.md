---
name: agent-engineering
description: Expert in the Multi-Agent Auditor system. Use this skill to create new agents, modify existing agent prompts/logic, debug agent interactions, and update the orchestration layer.
---

# Agent Engineering

## When to use this skill

- Creating a new specialized agent (e.g., "Description Agent", "Safety Agent").
- Modifying the prompt or logic of an existing agent (e.g., "Photo Agent", "Title Agent").
- Debugging agent failures or JSON parsing errors.
- Changing the orchestration flow (e.g., parallelization, conditional execution).
- Updating agent data schemas.

## Structure

The agent system is built on a strictly typed, inheritance-based architecture:

- **Base Class**: `app/services/agents/base_agent.py` (`BaseAgent`)
  - Handles timing, error wrapping, and standard response formatting.
  - All agents **must** inherit from this.
- **Schemas**: `app/schemas/agent_schemas.py`
  - Uses Pydantic to define Input (`AgentRequest`) and Output (`[Name]AgentResponse`) models.
  - Strict typing is enforced.
- **Implementations**: `app/services/agents/`
  - Each agent has its own file (e.g., `photo_agent.py`).
  - Logic resides in `async def _process_logic(self, request: AgentRequest)`.
- **Orchestrator**: `app/services/multi_agent_orchestrator.py`
  - Manages the lifecycle of an audit.
  - Handles dependency injection (passing results from Agent A to Agent B).
  - Aggregates final results.

## Workflow Rules

### 1. Creating a New Agent

1.  **Define Schema**:
    - Open `app/schemas/agent_schemas.py`.
    - Create a specific `AnalysisResult` model for the agent's findings.
    - Create a `[Name]AgentResponse` model inheriting from `BaseAgentResponse`.
    - Add the new response type to `MultiAgentAuditResult`.

2.  **Implement Agent Class**:
    - Create `app/services/agents/[name]_agent.py`.
    - Inherit from `BaseAgent`.
    - Initialize with `super().__init__(agent_name="...", response_class=...)`.
    - **Crucial**: Implement `_process_logic(self, request)`.
    - Use `self.gen_service.chat_with_usage(...)` for LLM calls.
    - Ensure the prompt requests JSON output matching your Schema.

3.  **Register in Orchestrator**:
    - Open `app/services/multi_agent_orchestrator.py`.
    - Import the new agent class.
    - Initialize it in `__init__`.
    - Add it to the execution flow in `run_audit`.

### 2. Modifying Prompts

- Locate the agent file in `app/services/agents/`.
- Prompts are typically defined in `_process_logic` or a helper method `_get_prompt`.
- **Constraint**: If you change the JSON structure requested in the prompt, you **must** update `app/schemas/agent_schemas.py` to match.

### 3. Orchestration Logic

- **Parallelism**: Use `asyncio.gather` for agents that don't depend on each other.
- **Context Passing**: Use `request.context` to pass data between agents.
  - *Example*: `request.context["photo_analysis"] = photo_res.analysis`
- **Error Handling**: The `BaseAgent` wraps exceptions. Check `response.status == "failure"` in the orchestrator before relying on the data.

## Inter-Agent Communication

This agent defines the **Contract** (Schemas) used by other agents.

- **To Backend Agent**:
  - The Pydantic models in `app/schemas/agent_schemas.py` are the **Binding Contract**.
  - Any change here **requires** notifying the `developing-backend-app` agent to update endpoints.
- **To Frontend Agent**:
  - The `MultiAgentAuditResult` structure dictates what the UI *can* display.
  - If you add a field here, ensure `developing-streamlit-app` knows to visualize it.

## Best Practices

- **Strict JSON**: Always instruct the LLM to return `response_mime_type: application/json`.
- **Type Safety**: Use Pydantic models for everything. Do not rely on unstructured dictionaries if possible.
- **Logging**: Use `logger.info` for high-level flow and `logger.error` for exceptions.
