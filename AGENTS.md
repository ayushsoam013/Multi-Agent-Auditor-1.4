# Multi-Agent Auditor - Developer & Agent Guide

This document outlines the architecture, coding standards, and workflows for the Multi-Agent Auditor project. Agents operating in this codebase **must** adhere to these guidelines.

## 1. Project Overview & Architecture

*   **Type**: Hybrid Application (FastAPI Backend + Streamlit Frontend).
*   **Goal**: Automated auditing using Multi-Agent Systems (Gemini/LiteLLM) and Vector Search (Qdrant).
*   **Key Constraints**:
    *   **Decoupling**: Frontend (`streamlit_app/`) **NEVER** accesses the database, vector store, or LLMs directly. It must consume the FastAPI backend.
    *   **Configuration**: All configuration (API keys, URLs) must be in `.env` and loaded via `app.core.config.settings`.

### Directory Structure Map
*   `app/` - **Backend (FastAPI)**
    *   `main.py` - Entry point.
    *   `api/v1/` - API Routes (Versioned).
    *   `services/` - Business Logic & Agent Orchestration.
    *   `models/` - Pydantic Data Models (DTOs).
    *   `core/` - Config & Security.
*   `streamlit_app/` - **Frontend (Streamlit)**
    *   `app.py` - Entry point.
    *   `pages/` - Individual tools/dashboards.
*   `tests/` - Manual integration tests & scripts.
*   `.agent/` - Agent skills and workflow definitions.

---

## 2. Build, Run & Test Commands

### Environment Setup
Ensure `.env` exists (copy from `.env.example`).
Dependencies are managed in `requirements.txt`.

### Running the Application
*   **Backend**:
    ```bash
    python run_fast.py
    # OR
    uvicorn app.main:app --reload
    ```
    *   Runs on: `http://localhost:8000`
    *   Docs: `http://localhost:8000/docs`

*   **Frontend**:
    ```bash
    python run_streamlit.py
    # OR
    streamlit run streamlit_app/app.py
    ```
    *   Runs on: `http://localhost:8501`

### Testing
Tests are currently implemented as standalone Python scripts using `fastapi.testclient`.

*   **Run a specific test suite**:
    ```bash
    python tests/test_audit_manual.py
    ```
    *   *Note*: Ensure `misc/sofa.jpg` exists for image audit tests.

---

## 3. Coding Standards & Guidelines

### General
*   **Type Hinting**: **MANDATORY**. Use standard Python type hints (`List`, `Optional`, `Dict`) and Pydantic models for all data structures.
*   **Formatting**: Adhere to PEP 8.
*   **Docstrings**: Required for all complex Service methods and API endpoints. Explain *why*, not just *what*.

### Backend (FastAPI)
*   **Architecture**: Follow the pattern: `Router` -> `Service` -> `Repository` (optional).
    *   **Routers** (`app/api/`): Handle HTTP parsing/validation only. Delegate logic to Services.
    *   **Services** (`app/services/`): Pure python logic. Dependency Injection preferred.
*   **Models**: Use `Pydantic` for `SchemaIn` (Requests) and `SchemaOut` (Responses).
*   **Async**: Use `async def` for all endpoints and I/O-bound service methods.
*   **Error Handling**: Raise `fastapi.HTTPException` with appropriate status codes (400, 404, 500) for client-facing errors.

### Frontend (Streamlit)
*   **API Integration**: Use `requests` library wrapped in `try/except` blocks.
    ```python
    try:
        resp = requests.get(f"{settings.API_BASE_URL}/endpoint")
        resp.raise_for_status()
    except Exception as e:
        st.error(f"API Error: {e}")
    ```
*   **State**: Use `st.session_state` for data persistence across reruns.
*   **UX**: Provide feedback (`st.spinner`, `st.success`) for all async operations.

---

## 4. Agent Protocols
*   **Context Awareness**: Always check `Gemini.md` files in `app/` and `streamlit_app/` for component-specific rules before modifying them.
*   **Skill Usage**: Refer to `.agent/skills/` for specific workflows like "Developing Backend App".
*   **Documentation**: If you change the architectural pattern, you **must** update the relevant `Gemini.md` file.
