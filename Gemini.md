# Multi-Agent Auditor - Project Guidelines (Gemini.md)

This document serves as the central hub for coding standards, architectural decisions, and rules for the Multi-Agent Auditor application.

## 1. Project Overview

This application represents a rigorous auditing POC leveraging Multi-Agent systems.

- **Frontend**: Streamlit (`streamlit_app/`) for the user interface and admin panels.
- **Backend**: FastAPI (`app/`) for the core logic, API endpoints, and heavy lifting.
- **Infrastructure**: Python-based, utilizing Qdrant for vector storage and LLMs (Gemini/LiteLLM) for intelligence.

## 2. Component-Specific Rules

Please refer to the detailed guidelines for each component before making changes:

- **[Backend Rules (FastAPI)](app/Gemini.md)**: Architecture, Pydantic models, Async conventions, API design.
- **[Frontend Rules (Streamlit)](streamlit_app/Gemini.md)**: UI components, API integration, State management.

## 3. General Development Workflow

1.  **Environment**: Ensure your `.env` file is configured (see `.env.example`).
2.  **Running the App**:
    - **Backend**: `python run_fast.py` (Starts FastAPI on port 8000).
    - **Frontend**: `python run_streamlit.py` (Starts Streamlit on default port).
3.  **Dependencies**: Managed via `requirements.txt`. Always update if you add new packages.
4.  **Version Control**:
    - Descriptive Commit Messages.
    - Feature branching is encouraged.

## 4. Architectural Principles

- **Decoupling**: The Streamlit frontend should NEVER access the database or logic directly. It must only consume the FastAPI endpoints.
- **Configurability**: All changing parameters (API keys, URLs, Thresholds) must be in `.env` or injected via dependency injection, not hardcoded.
- **Agentic Design**: When extending agent capabilities, define clear "Skills" or "Tools" in the backend that can be invoked via simple API calls.

## 5. Updates & Maintenance

- When adding a new feature, update both the `app/` (API) and `streamlit_app/` (UI) accordingly.
- Keep these `Gemini.md` files updated if architectural patterns change.
