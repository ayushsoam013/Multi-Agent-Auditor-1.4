# Deployment Guide (Render)

This application is configured for deployment on [Render](https://render.com).

## Prerequisities

- A [Render](https://render.com) account.
- GitHub repository connected to Render.

## Deployment Steps

1. **Create New Web Service**:
   - Go to Render Dashboard > New > Web Service.
   - Select your repository.

2. **Configuration**:
   - **Name**: `multi-agent-auditor` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `./start.sh`

3. **Environment Variables**:
   You **MUST** add the following environment variables in the Render Dashboard:

   | Variable | Value / Description |
   |----------|---------------------|
   | `GEMINI_API_KEY` | Your Google Gemini API Key |
   | `LITELLM_API_KEY` | (Optional) If using LiteLLM |
   | `API_BASE_URL` | `http://127.0.0.1:8000/api/v1` (Internal communication) |
   | `PORT` | Render automatically sets this (e.g., 10000). Streamlit uses it. |
   
   > **Note on `API_BASE_URL`**: Since the Frontend and Backend run in the *same* container (via `start.sh`), they communicate over `localhost`. Streamlit (Python) calls FastAPI via `http://127.0.0.1:8000`. The User's browser accesses Streamlit via the public URL.

## Troubleshooting

- **Backend not starting**: Check the Logs. `start.sh` waits 30s for port 8000.
- **502 Bad Gateway**: Ensure `start.sh` is executable (`chmod +x start.sh` locally before commit).
