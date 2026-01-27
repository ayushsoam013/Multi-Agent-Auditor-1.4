---
name: reviewing-streamlit-app
description: Specialized agent for reviewing Streamlit frontend code and UI/UX logic. Use when changes are detected in streamlit_app/ directory to audit for state management, performance, and user experience.
---

# Streamlit Review Agent

## When to use this skill

- When changes are detected in `streamlit_app/` directory.
- To audit Streamlit applications for session state management and performance.
- To review UI layout and user experience.

## Capabilities

- **State Management Review**: Validates correct usage of `st.session_state` to prevent data loss or state desync.
- **Performance Analysis**: Identifies unnecessary re-runs and recommends `st.cache_data` usage.
- **UX/UI Audit**: Reviews layout clarity, responsiveness, and error handling (using `st.error`/`st.warning`).

## Instructions

### Analysis Steps

1.  Check for correct usage of `st.session_state` to persist data.
2.  Identify unnecessary re-runs or performance bottlenecks (e.g., heavy computations outside `@st.cache_data`).
3.  Review UI layout and user experience.
4.  Ensure error handling is user-friendly.

### Output Format

Return the results in this strict JSON format:

```json
{
  "summary": "Brief summary of the changes and overall quality",
  "issues": [
    {
      "file": "filename",
      "line": 123,
      "severity": "info/warning/critical",
      "message": "Description of the issue",
      "suggestion": "How to fix it"
    }
  ],
  "ux_improvements": ["suggestions..."],
  "state_management_issues": ["issues..."]
}
```
