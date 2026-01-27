---
name: maintaining-documentation
description: Ensures project documentation remains synchronized with the implementation. Use to update AGENTS.md, Gemini.md, and other architectural docs after codebase modifications.
---

# Documentation Maintainer

Ensures that all project documentation remains synchronized with the actual implementation of the codebase.

## Workflow

1.  **Analyze Changes**: After any code modification, identify if the change impacts:
    - API endpoints or schemas.
    - Service layer architecture.
    - State management patterns.
    - Configuration/Environment variables.
    - Project structure (new directories/files).

2.  **Locate Docs**:
    - Check `AGENTS.md` for global changes.
    - Check `app/Gemini.md` for backend-specific changes.
    - Check `streamlit_app/Gemini.md` for frontend-specific changes.

3.  **Update Strategy**:
    - **Backend**: Update `app/Gemini.md` if new services, routers, or architectural patterns are introduced.
    - **Frontend**: Update `streamlit_app/Gemini.md` if new pages, state patterns, or UI components are added.
    - **Global**: Update `AGENTS.md` if build commands, dependencies, or high-level project goals change.

4.  **Verification**:
    - Ensure all links and paths in documentation are valid.
    - Verify that code examples in docs match the latest implementation.
    - Check for consistent naming and terminology across all doc files.

## Best Practices

- Keep documentation concise and focused on "Why".
- Use Markdown for structured formatting.
- Always include the "Intent" behind architectural decisions.
- Update documentation _immediately_ after a feature is completed or a bug is fixed that changes behavior.
