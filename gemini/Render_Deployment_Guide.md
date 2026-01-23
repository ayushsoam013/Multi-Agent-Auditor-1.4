# Render Deployment Guide - Multi-Agent Auditor

This guide outlines the procedure for deploying the Multi-Agent Auditor (FastAPI + Streamlit) on Render using a **Single-Service Strategy**. This approach is cost-effective and simplifies management by running both components in one container.

## 1. Deployment Architecture

- **Service Type**: Render Web Service
- **Runtime**: Python 3.9+
- **Process Management**:
    - **FastAPI**: Runs internally on `localhost:8000`.
    - **Streamlit**: Runs on the Render-assigned `$PORT` and acts as the public interface.
- **Internal Communication**: Streamlit connects to FastAPI via `http://localhost:8000/api/v1`.

## 2. Preparation

### `start.sh` Script
The `start.sh` script is the entry point for Render. It handles launching both processes:
```bash
#!/bin/bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

## 3. Render Configuration Steps

### A. Create New Web Service
1. Connect your GitHub repository to Render.
2. Select the repository for this project.

### B. Build & Start Settings
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `./start.sh`

### C. Environment Variables
You must configure the following environment variables in the Render Dashboard:

| Variable | Recommended Value | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.10.0` (or your preferred version) | Ensures correct Python runtime. |
| `API_BASE_URL` | `http://localhost:8000/api/v1` | Point Streamlit to the internal API. |
| `GEMINI_API_KEY` | `your_api_key_here` | **Required** for Gemini agents. |
| `LITELLM_API_KEY` | `your_api_key_here` | **Required** if using LiteLLM. |
| `ENVIRONMENT` | `prod` | Switches app to production mode. |

## 4. Best Practices for Render

1. **Headless Streamlit**: Always use `--server.headless true` to prevent Streamlit from trying to open a browser window in the server.
2. **Internal Binding**: Bind the FastAPI backend to `127.0.0.1` instead of `0.0.0.0` if you don't want the API exposed directly (since Render only routes the `$PORT` anyway).
3. **Health Checks**: Render's health check will monitor the Streamlit port. Since Streamlit depends on FastAPI, a successful load of the UI generally confirms both are up.
4. **Resources**: The Multi-Agent Auditor is memory-intensive during LLM orchestration. We recommend at least a **Starter** instance (512MB - 1GB RAM) rather than the Free tier for stable performance.

## 5. Troubleshooting

- **UI Loads but Data Fails**: Check if `API_BASE_URL` is set correctly to `http://localhost:8000/api/v1`.
- **Port Conflicts**: Ensure no other process is trying to bind to `$PORT`.
- **Memory Limits**: If the service restarts during an audit, check the "Events" tab in Render for "Out of Memory" errors.
