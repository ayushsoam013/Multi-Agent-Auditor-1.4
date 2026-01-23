# Frontend (Streamlit) Coding Standards & Rules

## 1. Structure

The frontend is a multipage Streamlit application.

- **Main Entry**: `streamlit_app/app.py`
- **Pages** (`streamlit_app/pages/`):
    - `1_Health_Check.py`: API and system status monitoring.
    - `3_Multi_Agent_Auditor.py`: Core UI for triggering audits.
    - `Chat.py`: LLM chat interface.

## 2. API Integration

- **Decoupling**: No direct backend logic or database access in the frontend. All data must come from the FastAPI backend.
- **Requests**: Use `requests` with standard error handling.
- **Configuration**: Load `API_BASE_URL` from the backend settings or environment.

## 3. UI/UX Guidelines

- **Feedback**: Use `st.spinner` for any operation taking > 0.5s.
- **Status Icons**: Use standard Streamlit status components (`st.success`, `st.error`, `st.info`).
- **Sidebar**: Use for global controls (e.g., LLM Provider selection).

## 4. State Management

- **Persistence**: Use `st.session_state` to keep user selections and results during the session.
- **Initializers**: Always check if a key exists in `st.session_state` before accessing it.

## 5. Execution

- **Standard Run**: `python run_streamlit.py`
- **Streamlit CLI**: `streamlit run streamlit_app/app.py`
