---
name: creating-opencode-agents
description: Helper for defining new OpenCode agents. Use to define new agent capabilities, create their markdown definitions in .opencode/agents/, and ensure they follow the project's agent architecture.
---

# OpenCode Agent Creator

## When to use this skill

- Creating a new agent definition in `.opencode/agents/`.
- Converting existing Python logic (e.g. from `app/services/agents/`) into an OpenCode Agent definition.
- Defining the capabilities, scope, and prompts for a new agent.

## Agent Definition Format

All OpenCode agents are defined in `.opencode/agents/<agent-name>.md`.
The file must start with a YAML frontmatter block:

```yaml
---
name: <agent-name-kebab-case>
description: <Short description for the Task tool>
compatibility: opencode
---
```

Followed by the agent documentation in Markdown:

```markdown
# <Agent Name Title>

## When to use this skill

- <Bullet points describing usage scenarios>

## Capabilities

- <What the agent can do>

## Instructions / Prompts

- <Detailed instructions on how the agent should behave, its system prompt, or logic>
```

## Instructions

1.  **Analyze Requirements**: Understand what the new agent needs to do.
2.  **Draft Definition**: Create the `.md` content with frontmatter.
3.  **Write File**: Save it to `.opencode/agents/<agent-name>.md`.

### Best Practices

1. **Naming**: Use kebab-case for the filename and the `name` field (e.g., `code-reviewer.md`, `backend-dev.md`).
2. **Description**: Keep it concise (under 200 characters) as it appears in the tool selection list.
3. **Clarity**: The markdown body serves as the "System Prompt" or "Manual" for the agent. Be specific about what tools it should use and how it should reason.
4. **Context**: If converting from Python, capture the essence of the `_process_logic` and the prompts used in the Python code.
