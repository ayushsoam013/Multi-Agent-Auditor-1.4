#!/bin/bash

# Start FastAPI backend in the background
# We bind to 127.0.0.1:8000 as it only needs to be accessible by the Streamlit app internally
echo "Starting FastAPI backend on localhost:8000..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 5

# Start Streamlit frontend in the foreground
# Streamlit will be exposed to the public internet via Render's $PORT
echo "Starting Streamlit frontend on port $PORT..."
streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
