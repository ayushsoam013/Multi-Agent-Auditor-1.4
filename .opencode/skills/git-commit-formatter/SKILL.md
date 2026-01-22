# Git Commit Formatter Skill

This agent is responsible for creating a git commit based on staged changes.

## Workflow
1. **Check Staged Changes**: Use `git status` or `git diff --cached` to see if there are any changes in the staging area.
2. **Handle Empty Staging**: If no changes are staged, inform the user and ask them to stage the files they want to commit. Terminate the task.
3. **Analyze Changes**: If changes are staged, use `git diff --cached` to analyze the exact modifications.
4. **Generate Commit Message**: Create a concise, relevant commit message grounded in the analyzed changes. Follow the Conventional Commits specification (e.g., `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`).
5. **Commit**: Execute `git commit -m "<message>"`.
6. **No Push**: Do NOT push the changes to any remote repository.
7. **No Extra Actions**: Do not perform resets, look back at history (unless necessary for context of the message), or any other tasks.

## Constraints
- Focus only on staged changes.
- Do not push.
- Do not modify the staging area (no `git add`). ALWAYS ask for permission before staging any files.
- If nothing is staged, notify the user and wait for them to stage files. NEVER automatically run `git add .` or similar commands.
- Keep the commit message grounded and relevant.
