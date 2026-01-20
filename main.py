import subprocess
import sys


def run_fastapi():
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    print(f"Running FastAPI: {' '.join(cmd)}")
    return subprocess.Popen(cmd)


def run_streamlit():
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app/app.py",
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
    ]
    print(f"Running Streamlit: {' '.join(cmd)}")
    return subprocess.Popen(cmd)


if __name__ == "__main__":
    print(f"Using python: {sys.executable}")
    print("🚀 Starting FastAPI and Streamlit...")
    api = run_fastapi()
    ui = run_streamlit()

    api.wait()
    ui.wait()
