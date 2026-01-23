---
name: code-review-agent
description: Orchestrator agent that analyzes git diffs and delegates review tasks to backend and frontend specialists.
compatibility: opencode
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

## Instructions / Prompts
This agent acts as a manager and does not typically query the LLM directly for the review itself. Instead, it follows this logic:

1.  **Context Verification**: Checks if `git_diff` is present in the request context. If not, it runs `git diff` (unstaged) and `git diff --staged` to capture all changes.
2.  **Diff Splitting**:
    - Scans the diff for file paths.
    - Lines containing `a/streamlit_app/` or `b/streamlit_app/` are routed to the **Streamlit Reviewer**.
    - Lines containing `a/app/`, `b/app/`, or `requirements.txt` are routed to the **Backend Reviewer**.
3.  **Parallel Execution**:
    - Invokes `BackendReviewAgent` with the backend portion of the diff.
    - Invokes `StreamlitReviewAgent` with the streamlit portion of the diff.
4.  **Result Aggregation**:
    - Collects `issues` from both sub-agents.
    - Sums up the token costs.
    - Returns a composite summary (e.g., "Backend: 3 issues. Frontend: 2 issues.").
