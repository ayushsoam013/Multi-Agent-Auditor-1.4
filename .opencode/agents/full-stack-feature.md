---
name: full-stack-feature
description: Orchestrates complex features requiring changes across Agents, Backend, and Frontend. Coordination skill that triggers other specialized skills in the correct order.
compatibility: opencode
---

# Full Stack Feature Implementation

## When to use this skill

- Implementing end-to-end features (e.g., "Add a Safety Check Agent and show results in the UI").
- When a request spans multiple domains (Architecture + API + UI).
- To coordinate the "Hand-off" between specialized agents.

## Workflow & Communication Protocol

This skill acts as the **Project Manager**. It does not write code directly but delegates to specialized skills.

### Phase 1: Architecture & Intelligence (`agent-engineering`)
**Goal**: Define the "Brain" and Data Structures.
1.  **Trigger**: If the request involves new reasoning, AI logic, or orchestration changes.
2.  **Input**: User Requirements.
3.  **Output**:
    - Updated `app/schemas/agent_schemas.py` (The Contract).
    - New/Modified Agents in `app/services/agents/`.
    - Orchestrator updates.
4.  **Handoff**: The **Schema** (`agent_schemas.py`) is the source of truth passed to the Backend.

### Phase 2: Backend Services (`developing-backend-app`)
**Goal**: Expose the Intelligence via API.
1.  **Trigger**: Once Schemas are defined.
2.  **Input**: `agent_schemas.py` and Service Logic.
3.  **Output**:
    - New/Updated `app/services/[name]_service.py`.
    - API Endpoints in `app/api/v1/endpoints/`.
    - `AGENTS.md` updates if new commands are needed.
4.  **Handoff**: The **API Endpoint URL** and **JSON Response Format** are passed to the Frontend.

### Phase 3: Frontend Experience (`developing-streamlit-app`)
**Goal**: Visualize the Results.
1.  **Trigger**: Once API is stable.
2.  **Input**: API Endpoint and Response JSON structure.
3.  **Output**:
    - Streamlit Page updates (`streamlit_app/pages/`).
    - UI Components (Cards, Tables, Expanders).
    - Error Handling for the specific API codes.

## Coordination Instructions

To execute a Full Stack Feature, proceed sequentially:

1.  **Plan**: Break the user request into the 3 phases above.
2.  **Execute Phase 1**:
    - Load `agent-engineering` skill.
    - Implement changes.
    - Verify `agent_schemas.py`.
3.  **Execute Phase 2**:
    - Load `developing-backend-app` skill.
    - Implement API.
    - Test manually with `tests/test_...py`.
4.  **Execute Phase 3**:
    - Load `developing-streamlit-app` skill.
    - Connect UI to the new API.
    - Verify End-to-End.

## Communication Rules

- **Shared Context**: All agents share the project root and `.env`.
- **Contract First**: Changes in Phase 1 (Schemas) **dictate** Phase 2 and 3. Phase 3 cannot start until Phase 1 schemas are stable.
- **Verification**: Each phase must pass its specific checklist before moving to the next.
