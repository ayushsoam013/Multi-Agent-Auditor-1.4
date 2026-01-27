# Vibe Coding in Multi-Agent Auditor

The creation of this project exemplifies "Vibe Coding"—a high-level, intent-driven development process where a human orchestrator provides the "vibe" (intent) and a sophisticated network of specialized agents handles the execution, refinement, and verification.

## Core Principles

### 1. Orchestrated Specialization (The "Brain" vs. The "Hands")
Instead of relying on a single general-purpose prompt, the project uses a **hierarchical agent system**. A "Project Manager" agent (`full-stack-feature`) receives the high-level intent and decomposes it into sub-tasks for specialized agents. This separation of concerns allows for deep domain expertise in each layer of the stack.
*   **Example**: When a user asks for a new feature, `full-stack-feature` coordinates a hand-off: first to `agent-engineering` to design the AI logic, then to `developing-backend-app` for API implementation, and finally to `developing-streamlit-app` for UI visualization.

### 2. Contract-Driven Implementation (Grounding the "Vibe")
To ensure that "vibes" translate into reliable software, the system uses **Schema-First Development**. The `agent-engineering` agent acts as the architect, defining strict Pydantic models in `app/schemas/agent_schemas.py` before any code is written. These schemas act as the "Binding Contract" that all other agents must follow.
*   **Example**: The `agent-engineering` agent ensures that if a new "Safety Agent" is created, its output format is strictly defined. This allows the backend and frontend agents to build their components with 100% certainty about the data structures they will receive.

### 3. Autonomous Quality Loops (Verification of Intent)
Vibe coding is prone to "hallucinations" or drift if not verified. This project mitigates this through **autonomous feedback loops**. Agents like `code-review-agent` and `test-driven-development` act as the project's immune system, reviewing changes against established standards (`Gemini.md` files) and ensuring the "vibe" hasn't compromised code quality.
*   **Example**: The `code-review-agent` automatically splits a git diff into backend and frontend sections, delegating them to specialized reviewers (`BackendReviewAgent` and `StreamlitReviewer`) who verify that the new code adheres to the specific linting and architectural rules defined for those environments.

## Agent Architecture Summary

| Agent Type | Role in "Vibe Coding" | Example Task |
| :--- | :--- | :--- |
| **Full-Stack Orchestrator** | **Manager**: Coordinates the end-to-end flow of a feature. | "Add a new auditing agent and show its results on the dashboard." |
| **Agent Engineer** | **Architect**: Designs data contracts and AI reasoning logic. | "Update `agent_schemas.py` to include token usage tracking." |
| **Code Reviewer** | **Quality Control**: Ensures the "vibe" meets production standards. | "Analyze the current git diff for security flaws in the API." |
| **Frontend/Backend Devs** | **Specialists**: Implement specific logic within their domain. | "Create a new Streamlit page to visualize the audit history." |
