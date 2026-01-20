# Frontend (Streamlit) Coding Standards & Rules

## 1. Structure

The frontend is a multipage Streamlit application.

- **Entry Point**: `streamlit_app/app.py`.
- **Pages**: Additional tools and views reside in `streamlit_app/pages/`.
- **Logic**: Keep UI code separate from backend API calls where possible.

## 2. API Integration

- **Communication**: All data should be fetched from the FastAPI backend. Avoid direct DB access from Streamlit.
- **Configuration**: Use `API_BASE_URL` (default: `http://localhost:8000/api/v1`) for all requests.
- **Error Handling**: Wrap `requests` calls in `try/except` blocks to handle connection errors gracefully.
  ```python
  try:
      response = requests.get(f"{API_BASE_URL}/endpoint")
      response.raise_for_status()
      data = response.json()
  except Exception as e:
      st.error(f"Failed to fetch data: {e}")
  ```

## 3. State Management

- **Session State**: Use `st.session_state` to share variables between reruns and across pages.
  - Initialize state variables at the top of the file if they don't exist.

## 4. UI/UX Guidelines

- **Layout**: Use `st.columns`, `st.expander`, and `st.tabs` to organize dense information.
- **Sidebar**: Use `st.sidebar` for navigation controls, global filters, and configuration (like LLM Provider selection).
- **Feedback**: Provide immediate user feedback (e.g., `st.success`, `st.spinner` during API calls).

## 5. Caching

- **Performance**: Use `@st.cache_data` for expensive data fetching operations (e.g., loading large datasets).
- **Resources**: Use `@st.cache_resource` for loading ML models or database connections if applicable (though strictly backend handling is preferred).

## 6. Execution

- **Running**: Use `python run_streamlit.py` or `streamlit run streamlit_app/app.py`.
