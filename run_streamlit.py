import subprocess
import sys

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
    subprocess.run(cmd)

if __name__ == "__main__":
    run_streamlit()
