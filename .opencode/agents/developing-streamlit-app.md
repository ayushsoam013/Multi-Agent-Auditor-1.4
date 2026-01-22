---
name: developing-streamlit-app
description: Specialized agent for building polished, responsive, and robust Streamlit frontend applications. Focuses on UX, error handling, and secure backend integration in streamlit_app directory.
compatibility: opencode
---

# Developing Streamlit App

## When to use this skill

- Creating new interactive dashboards or tools (`streamlit_app/pages/`).
- Improving User Experience (UX) with loaders, status updates, and clean layouts.
- Integrating with Backend APIs securely.
- Handling connection errors and API failures gracefully.

## Context & Architecture

- **Root**: `streamlit_app/`
- **Entry**: `streamlit_app/app.py`
- **Pages**: `streamlit_app/pages/`
- **Backend Communication**: Strictly via `requests` to backend API. **NO** direct DB/LLM access.

## Workflow Rules

### 1. Robust API Integration

- **Pattern**:
  ```python
  try:
      with st.spinner("Processing..."):
          response = requests.post(f"{API_BASE_URL}/...", json=payload, timeout=30)
          response.raise_for_status()
          data = response.json()
          # Process data
  except requests.exceptions.ConnectionError:
      st.error("Cannot connect to backend. Is it running?")
  except requests.exceptions.HTTPError as e:
      st.error(f"API Error: {e.response.text}")
  except Exception as e:
      st.error(f"Unexpected Error: {e}")
  ```
- **Timeout**: Always set a timeout on requests to prevent hanging UIs.

### 2. UX Best Practices

- **Feedback**: Immediate visual feedback for user actions (spinners, success banners).
- **State Management**: Use `st.session_state` to persist data between re-runs (e.g., keeping a chat history or form inputs).
- **Layout**:
  - Use `st.columns` for grid layouts.
  - Use `st.expander` to hide raw data or advanced settings.
  - Use `st.tabs` for organizing complex views.

### 3. Error Handling & Edge Cases

- **Empty States**: Handle cases where API returns empty lists or nulls. Display friendly messages ("No data found") instead of crashing.
- **Validation**: Validate user inputs *before* sending to the backend (e.g., "Please upload a file").
- **Resilience**: If an API call fails, the app should not crash. It should show an error and allow retrying.

## Inter-Agent Communication

This agent is the **Consumer** of the work produced by `developing-backend-app`.

- **From Backend Agent**:
  - Rely on the API Contract (Endpoints & JSON structure) provided by the Backend.
  - Do not assume fields exist if they are not in the Backend Schema (`app/schemas/`).
- **Feedback Loop**:
  - If the UI requires new data, request changes via the `full-stack-feature` or `agent-engineering` skill, do not mock data permanently.

## Checklist for Polished UI

1. [ ] **Separation of Concerns**: Is business logic delegated to the backend?
2. [ ] **Feedback Loops**: Does the user know the system is working?
3. [ ] **Error Grace**: Do errors look intentional and helpful?
4. [ ] **State Preservation**: Does the app "remember" inputs effectively?
5. [ ] **Responsiveness**: Are heavy computations (if any) cached or offloaded?
