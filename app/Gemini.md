# Backend (FastAPI) Coding Standards & Rules

## 1. Architecture Overview

The backend follows a layered architecture to ensure separation of concerns.

- **API Layer** (`app/api`): Versioned routers (`v1/`) handling HTTP parsing and validation.
- **Service Layer** (`app/services`): Business logic and Agent orchestration.
    - `MultiAgentOrchestrator`: Coordinates multiple specialized agents.
    - `LLMManager`: Manages different LLM providers (Gemini, LiteLLM).
- **Schema Layer** (`app/schemas`): Pydantic models for data validation.
- **Core** (`app/core`): Centralized configuration via `pydantic-settings`.

## 2. API Development Rules

- **Routers**: Register all new routers in `app/api/v1/api.py`.
- **Async**: Use `async def` for all path operations and I/O-bound service methods.
- **Versioning**: Always prefix paths with `/api/v1`.
- **CORS**: Managed in `app/main.py`. Default is permissive for development.

## 3. Data Validation & Types

- **Pydantic**: Use for all Request/Response models.
- **Type Hinting**: Mandatory. Use `typing` module for complex types.
- **LSP Awareness**: Pay attention to type compatibility when using external libraries like `google-genai` or `litellm`. Avoid `Any` where possible, use `cast` if necessary for library-specific type mismatches.

## 4. Error Handling

- **Consistent Responses**: Use `fastapi.HTTPException` for client-side errors.
- **Logging**: Use `logging.getLogger(__name__)`. Log stack traces for 500 errors.
- **Agent Failures**: Specialized agents should return a `status="failure"` response rather than raising unhandled exceptions in the orchestrator.

## 5. Execution

- **FastAPI**: `python run_fast.py`
- **Uvicorn**: `uvicorn app.main:app --reload`
- **Docs**: Access `/docs` or `/redoc` for interactive API exploration.
