---
name: test-driven-development
description: Facilitates Test Driven Development (TDD) by writing comprehensive tests BEFORE implementation. Orchestrates the Red-Green-Refactor cycle by coordinating with development agents.
compatibility: opencode
---

# Test Driven Development (TDD)

## When to use this skill

- When the user explicitly asks for "TDD" or "Test Driven Development".
- When a feature is complex and requires strict verification (e.g., "Add a new validation rule for 100% compliance").
- Before implementing any "Critical Path" feature where regression is a high risk.
- To ensure 100% coverage of a requested feature's requirements *before* writing production code.

## Workflow Rules

### Phase 1: Red (Test Creation)

1.  **Analyze Intent**: Understand the feature requirements deeply. What is the Input? What is the Expected Output? What are the Edge Cases?
2.  **Scaffold Test**: Create a new test file in `tests/` (e.g., `tests/test_[feature].py`).
3.  **Write Assertions**:
    - Use `fastapi.testclient.TestClient`.
    - Mock inputs (images, JSON).
    - Assert strictly: Status Codes, JSON Schema, Error Messages.
    - **Cover Edge Cases**: Empty inputs, invalid types, boundary values.
4.  **Verify Failure**: Run the test. It **MUST** fail (or error out) because the feature doesn't exist yet. This confirms the test is valid.

### Phase 2: Green (Implementation)

1.  **Delegate**: Trigger the appropriate development skill:
    - `developing-backend-app` for API/Logic.
    - `agent-engineering` for new Agents.
2.  **Instruction**: Pass the *Test File Path* and *Requirements* to the dev agent. "Implement this feature so that `tests/test_[feature].py` passes."
3.  **Iterate**:
    - Run Test -> Fail -> Read Error -> Fix Code -> Run Test.
    - Repeat until **ALL** assertions pass.

### Phase 3: Refactor (Optimization)

1.  **Review**: Once green, look for code smells or optimization opportunities.
2.  **Refactor**: Trigger dev agents to clean up code while ensuring tests stay Green.
3.  **Final Verify**: Run the full test suite to ensure no regressions.

## Inter-Agent Communication

- **To Dev Agents**:
  - You are the **Quality Gatekeeper**.
  - Do not allow the dev agent to mark a task as "Done" until your specific test suite passes.
  - Provide raw test output logs to the dev agent so they know exactly *why* it failed.

## Checklist for TDD

1. [ ] **Intent Coverage**: Do the tests cover all acceptance criteria mentioned by the user?
2. [ ] **Edge Case Coverage**: Did you test negative scenarios (e.g., 400 Bad Request)?
3. [ ] **Independence**: Is the test self-contained? Does it clean up after itself?
4. [ ] **Red-Green Confirmed**: Did you verify it failed before it passed?
