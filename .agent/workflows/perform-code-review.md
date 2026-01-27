---
description: Perform a full-stack code review of current changes using specialized agents.
---

This workflow automates the analysis of current git changes.

1. **Capture Changes**
   - Run `git diff` and `git diff --staged` to get the current state of changes.

2. **Route to Specialists**
   - Use the `reviewing-code-changes` skill to split the diff into Backend and Frontend parts.
   - Run `reviewing-backend-code` on any changes in `app/` or `requirements.txt`.
   - Run `reviewing-streamlit-app` on any changes in `streamlit_app/`.

3. **Aggregate Feedback**
   - Collect and present a unified report of issues, security concerns, and performance tips.
   - Summarize the overall quality of the changes.

4. **Iterate**
   - Address the critical issues before committing.
