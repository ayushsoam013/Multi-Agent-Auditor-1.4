---
name: reviewing-code-changes
description: Orchestrates git diff analysis and delegates review tasks to backend and frontend specialists. Use when a user requests a code review of current changes to provide a unified full-stack audit.
---

# Code Review Agent

## When to use this skill

- When a user requests a code review of the current changes.
- To orchestrate a full stack review involving both backend and frontend components.
- To automatically split a git diff into relevant sections for specialized analysis.

## Capabilities

- **Git Diff Analysis**: Fetches staged and unstaged changes from git.
- **Diff Splitting**: Intelligently splits the diff into Backend (`app/`) and Frontend (`streamlit_app/`) segments.
- **Orchestration**: Delegates analysis to `BackendReviewAgent` and `StreamlitReviewAgent` in parallel.
- **Aggregation**: Combines findings from sub-agents into a unified report.

## Instructions

This agent acts as a manager and follows this logic:

1.  **Context Verification**: Checks if `git_diff` is present in the request context. If not, it runs `git diff` (unstaged) and `git diff --staged` to capture all changes.
2.  **Diff Splitting**:
    - Scans the diff for file paths.
    - Lines containing `a/streamlit_app/` or `b/streamlit_app/` are routed to the **Streamlit Reviewer**.
    - Lines containing `a/app/`, `b/app/`, or `requirements.txt` are routed to the **Backend Reviewer**.
3.  **Parallel Execution**:
    - Invokes `reviewing-backend-code` with the backend portion of the diff.
    - Invokes `reviewing-streamlit-app` with the streamlit portion of the diff.
4.  **Result Aggregation**:
    - Collects `issues` from both sub-agents.
    - Sums up the token costs.
    - Returns a composite summary (e.g., "Backend: 3 issues. Frontend: 2 issues.").
