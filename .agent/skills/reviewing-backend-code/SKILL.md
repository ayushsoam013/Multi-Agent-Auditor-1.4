---
name: reviewing-backend-code
description: Specialized agent for reviewing Python backend code (FastAPI, Pydantic, AsyncIO). Use when changes are detected in app/ directory or requirements.txt to audit for security, performance, and best practices.
---

# Backend Review Agent

## When to use this skill

- When changes are detected in `app/` directory or `requirements.txt`.
- To audit Python code for security, performance, and best practices.
- To verify Pydantic models and strict typing usage.

## Capabilities

- **Code Quality Analysis**: Identifies bugs, logic errors, and race conditions.
- **Security Audit**: Checks for SQL injection, XSS, insecure dependencies, and secret exposure.
- **Performance Tuning**: Suggests async usage improvements, database query optimizations, and caching strategies.
- **Type Checking**: Verifies adherence to strict typing and Pydantic validation.

## Instructions

### Analysis Steps

1.  Identify potential bugs, logic errors, or race conditions.
2.  Check for security vulnerabilities.
3.  Suggest performance improvements.
4.  Verify strict typing.

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
  "security_concerns": ["concerns..."],
  "performance_tips": ["tips..."]
}
```
