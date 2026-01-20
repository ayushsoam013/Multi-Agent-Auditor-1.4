# Backend (FastAPI) Coding Standards & Rules

## 1. Architecture Overview

The backend follows a strict layered architecture to ensure separation of concerns and maintainability.

- **API Layer** (`app/api`): Handles HTTP requests, router registration, and request validation.
- **Service Layer** (`app/services`): Contains business logic. Services should be dependency-injected where possible.
- **Repository Layer** (`app/repositories` - optional): Handles database interactions (e.g., Qdrant, SQL).
- **Core** (`app/core`): Configuration, security, and logging.

## 2. API Development Rules

- **Routers**: All new endpoints must be defined in routers. Do NOT add routes directly to `main.py`.
- **Registration**: Register new routers in `app/api/v1/api.py`.
- **Versioning**: All API paths must include the version prefix (e.g., `/api/v1/...`).
- **Async/Await**: Use `async def` for all path operation functions unless blocking I/O is strictly necessary and handled efficiently.

## 3. Data Validation & Models

- **Pydantic**: Use Pydantic models for all Request bodies (`SchemaIn`) and Response bodies (`SchemaOut`).
- **Type Hinting**: Strictly use Python type hints (`List[str]`, `Optional[int]`, etc.) for function arguments and return types.

## 4. Configuration

- **Settings**: Do not hardcode secrets or configuration changes. Use `app.core.config.settings` which loads from `.env`.
- **Environment Variables**: New configuration items should be added to `.env.example` and the `Settings` class.

## 5. Error Handling

- **Exceptions**: Use `fastapi.HTTPException` for client-facing errors.
- **Status Codes**: Return appropriate HTTP status codes (200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Internal Error).

## 6. Deployment & Execution

- **Entry Point**: The application entry point is `app/main.py`.
- **Running**: Use `python run_fast.py` or `uvicorn app.main:app --reload`.

## 7. LLM Integration

- **Providers**: Supports switching between providers (Gemini, LiteLLM). Ensure logic respects the `current_provider` config.
