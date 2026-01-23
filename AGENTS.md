# Multi-Agent Auditor - Agentic Coding Guide

This document defines the architecture, coding standards, and operational protocols for the Multi-Agent Auditor project. All agentic coding assistants **must** strictly adhere to these guidelines.

## 1. Project Overview & Architecture

*   **Type**: Hybrid Application (FastAPI Backend + Streamlit Frontend).
*   **Goal**: Automated auditing using Multi-Agent Systems (Gemini/LiteLLM).
*   **Key Constraints**:
    *   **Decoupling**: Frontend (`streamlit_app/`) **NEVER** interacts with the database or LLMs directly. It communicates solely via the FastAPI backend.
    *   **Configuration**: Secrets and environment-specific settings must reside in `.env` and be accessed via `app.core.config.settings`.

### Directory Map
*   `AGENTS.md`: Global coding guide (this document).
*   `AGENTS_PROMPTS.md`: Detailed breakdown of all agents, their execution order, and specific LLM prompts.
*   `app/`: Backend (FastAPI) logic.
    *   `api/v1/`: Versioned API endpoints and router definitions.
    *   `services/`: Business logic, agent orchestration, and LLM integrations.
    *   `schemas/`: Pydantic data models for validation and serialization.
    *   `core/`: Core configuration, security, and shared utilities.
*   `streamlit_app/`: Frontend (Streamlit) UI.
    *   `app.py`: Main entry point.
    *   `pages/`: Individual dashboard pages and tools.
*   `tests/`: Integration and unit tests (mostly standalone scripts).
*   `.opencode/`: Definitions for agent skills and workflow automations.

---

## 2. Build, Run & Test Commands

### Environment Setup
1.  **Dependencies**: `pip install -r requirements.txt`
2.  **Environment**: Ensure `.env` is populated (see `.env.example`).

### Execution
*   **Backend**: `python run_fast.py` (Runs on port 8000).
*   **Frontend**: `python run_streamlit.py` (Runs on port 8501).
*   **Docs**: Interactive API documentation is available at `http://localhost:8000/docs`.

### Testing & Verification
*   **Run All Tests**: `pytest` (if configured) or run individual scripts:
    ```bash
    python tests/test_audit_manual.py
    ```
*   **Linting/Formatting**: Use `ruff` for fast linting and formatting:
    ```bash
    ruff check .    # Lint
    ruff format .   # Format
    ```

---

## 3. Coding Standards & Style

### 3.1. General Principles
*   **Type Hinting**: **STRICTLY MANDATORY**. Use `typing` module (`List`, `Dict`, `Optional`, `Any`) and Pydantic models.
*   **Async First**: Use `async def` for all I/O-bound operations.
    ```python
    async def fetch_data(item_id: str) -> Optional[ItemSchema]:
        # Implementation
        pass
    ```
*   **Documentation**: Provide docstrings explaining the *intent* (the "why").

### 3.2. Import Conventions
Follow this specific order, separated by a single newline:
1.  **Standard Library** (alphabetical)
2.  **Third-Party Libraries** (alphabetical)
3.  **Local Application Modules** (alphabetical, absolute imports)

Example:
```python
import asyncio
import logging

from fastapi import FastAPI
import streamlit as st

from app.core.config import settings
from app.services.audit_service import AuditService
```

### 3.3. Naming Conventions
*   **Classes**: `PascalCase` (e.g., `AuditService`, `MultiAgentOrchestrator`).
*   **Functions/Variables**: `snake_case` (e.g., `run_audit_task`, `audit_id`).
*   **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `API_V1_STR`).
*   **Pydantic Models**: `SchemaIn` for requests, `SchemaOut` for responses.

### 3.4. Error Handling
*   **API Layer**: Raise `fastapi.HTTPException`.
*   **Service Layer**: Use `try/except` with granular exception catching.
    ```python
    try:
        result = await agent.process(request)
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return ErrorResponse(status="failure", message=str(e))
    ```
*   **Cost Tracking**: All agents must report token usage and calculated costs in their response metadata.

### 3.5. Frontend (Streamlit) Specifics
*   **API Wrapper**: Wrap `requests` calls in `try/except`.
*   **UX**: Use `st.spinner` and `st.session_state`.

---

## 4. Agent Operational Protocols

### 4.1. Contextual Awareness
Before modifying code, check for local rules:
*   `app/Gemini.md`: Rules specific to backend logic.
*   `streamlit_app/Gemini.md`: Rules specific to the frontend UI.
*   `.opencode/skills/`: Specialized skills for complex workflows.

### 4.2. Workflow Automation & Maintenance
*   **Documentation**: Every architectural change requires an update to the relevant `Gemini.md` and potentially `AGENTS.md`.
*   **Skills**: Use the `docs-maintainer` skill in `.opencode/skills/docs-maintainer/` to ensure documentation parity.
*   **Commit Style**: Follow the `git-commit-formatter` skill for standardized commit messages.

### 4.3. Creating New Skills
When adding new agentic workflows, create a new directory in `.opencode/skills/<skill-name>/` containing a `SKILL.md` file that defines the workflow steps and best practices. This ensures scalability of the agent's capabilities.
