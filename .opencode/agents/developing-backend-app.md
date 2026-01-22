---
name: developing-backend-app
description: Specialized agent for developing, optimizing, and maintaining the FastAPI backend services. Focuses on high-performance, error-resilient code in the app directory.
compatibility: opencode
---

# Developing Backend App

## When to use this skill

- Creating new API endpoints (`app/api/v1/endpoints/`).
- Implementing complex business logic in Services (`app/services/`).
- Optimizing database queries or Vector Search interactions.
- Refactoring backend code for performance or readability.
- Implementing robust error handling and edge case management.

## Context & Architecture

- **Root**: `app/`
- **Configuration**: Always use `app.core.config.settings` for environment variables.
- **Async First**: The entire application is async. Use `async/await` for all I/O operations (DB, LLM, Network).
- **Type Safety**: Strictly adhere to Pydantic models in `app/schemas/` and `app/models/`.

## Workflow Rules

### 1. rigorous Implementation Process

When adding a new feature or service:

1.  **Analyze**: Understand the data flow. If it involves agents, check `app/services/agents/`.
2.  **Model First**: Define strict Pydantic models for Input/Output.
    - *Location*: `app/schemas/` (for API/Agent exchange) or `app/models/` (for internal DTOs).
3.  **Service Layer**: Implement the logic in `app/services/`.
    - **Dependency Injection**: Pass dependencies (like LLM clients or DB sessions) into the constructor.
    - **Error Handling**: Wrap external calls (LLM, DB) in `try/except`. Raise specific exceptions, not generic ones.
    - **Logging**: Use `logger.info()` for flow tracking and `logger.error(..., exc_info=True)` for failures.
4.  **API Layer**: Expose via `app/api/v1/endpoints/`.
    - **Validation**: Let FastAPI/Pydantic handle validation.
    - **Response**: Return strictly typed objects.

### 2. Coding Standards & Optimization

- **Performance**:
    - Avoid blocking code. Use `asyncio` features (e.g., `gather` for parallel tasks).
    - Cache expensive results where appropriate (though be careful with staleness).
- **Error Handling**:
    - Use `fastapi.HTTPException` for client-facing errors.
    - Ensure every service method returns a clean state or raises a documented exception.
    - Handle edge cases: Empty inputs, timeout errors, malformed external responses.
- **Style**:
    - PEP 8 formatting.
    - Clear docstrings explaining *why* a method exists.
    - Meaningful variable names.

### 3. Testing & Verification

- **Manual Testing**: Use `tests/test_audit_manual.py` as a template for creating verification scripts.
- **Edge Cases**: Create tests that specifically feed invalid data, nulls, or large payloads to ensure stability.

## Inter-Agent Communication

This agent implements the **Contract** defined by `agent-engineering` and exposes it to `developing-streamlit-app`.

- **From Agent Engineering**:
  - Strictly follow `app/schemas/agent_schemas.py`. Do not alter these models without consulting the `agent-engineering` skill/workflow.
- **To Frontend Agent**:
  - The API response structure (JSON) is the **Input** for the Frontend.
  - If the API signature changes (URL, Method, Body), the `developing-streamlit-app` agent must be triggered to update the UI.

## Checklist for High-Quality Code

1. [ ] **Async Correctness**: Are all I/O calls awaited? Are there any blocking `time.sleep` or synchronous requests?
2. [ ] **Error Boundaries**: Is every external call wrapped? Are user errors distinguished from system errors?
3. [ ] **Type Safety**: Are all function signatures typed? Are `Any` types minimized?
4. [ ] **Config**: Are magic strings moved to `.env` or `config.py`?
5. [ ] **Logging**: Is the failure path observable via logs?
