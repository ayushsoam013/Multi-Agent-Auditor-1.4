"""
Run Multi-Agent-Auditor in Production mode.
Usage: python main_prod.py [--no-ngrok] [--backend-port PORT] [--frontend-port PORT]
"""
import subprocess
import time
import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def log(msg):
    """Print message with flush for real-time output."""
    print(msg, flush=True)

# Default production ports
DEFAULT_BACKEND_PORT = 8002
DEFAULT_FRONTEND_PORT = 8503

def safely_end_ngrok():
    """Attempts to safely kill existing ngrok processes/tunnels."""
    log("🧹 Cleaning up existing ngrok tunnels...")
    try:
        from pyngrok import ngrok
        for tunnel in ngrok.get_tunnels():
            ngrok.disconnect(tunnel.public_url)
        ngrok.kill()
    except Exception:
        pass
    
    # Fallback to system taskkill for stubborn processes on Windows
    if os.name == 'nt':
        try:
            subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], 
                          capture_output=True, shell=True)
        except Exception:
            pass
    log("   ✅ Tunnels cleared.")

def run_backend(port):
    """Start FastAPI backend server."""
    log(f"\n📦 Starting FastAPI backend on port {port}...")
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    time.sleep(3)
    
    if backend_proc.poll() is None:
        log("   ✅ Backend started!")
        return backend_proc
    else:
        log("   ❌ Backend failed to start. Check app/main.py for errors.")
        sys.exit(1)

def run_frontend(port):
    """Start Streamlit frontend server."""
    log(f"\n🎨 Starting Streamlit frontend on port {port}...")
    frontend_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app/app.py",
        "--server.port",
        str(port),
        "--server.address",
        "0.0.0.0",
    ]
    
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    time.sleep(3)
    
    if frontend_proc.poll() is None:
        log("   ✅ Frontend started!")
        return frontend_proc
    else:
        log("   ❌ Frontend failed to start. Check streamlit_app/app.py for errors.")
        sys.exit(1)

def create_tunnels(frontend_port):
    """Create ngrok tunnel for the frontend."""
    log("\n🌐 Creating public tunnel...")
    
    try:
        from pyngrok import ngrok
        
        # Safely end any existing tunnel first
        safely_end_ngrok()
        time.sleep(1)
        
        # Get ngrok auth token from environment
        ngrok_token = os.getenv("NGROK_AUTH_TOKEN")
        if ngrok_token:
            ngrok.set_auth_token(ngrok_token)
            log("   🔑 Auth token applied.")
        else:
            log("   ⚠️  No NGROK_AUTH_TOKEN found in environment variables.")
            log("   ℹ️  Continuing with default ngrok settings (limited sessions).")
        
        # Get optional static domain for frontend from environment
        frontend_domain = os.getenv("NGROK_FRONTEND_DOMAIN")
        
        # Create frontend tunnel
        frontend_kwargs = {"addr": frontend_port, "proto": "http"}
        if frontend_domain:
            frontend_kwargs["domain"] = frontend_domain
            log(f"   🌍 Using static frontend domain: {frontend_domain}")
        
        public_url = ngrok.connect(**frontend_kwargs).public_url
        
        log("\n" + "="*60)
        log("🎉 PUBLIC ACCESS READY!")
        log(f"📱 SHARE THIS URL: {public_url}")
        log("="*60)
        
        return public_url
        
    except Exception as e:
        log(f"\n⚠️  Ngrok failed: {e}")
        log("   Access via Local URL instead.")
        return None

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    parser = argparse.ArgumentParser(
        description="Run Multi-Agent-Auditor in Production mode."
    )
    parser.add_argument(
        "--no-ngrok", 
        action="store_true", 
        help="Disable ngrok tunnel"
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=DEFAULT_BACKEND_PORT,
        help=f"Custom backend port (default: {DEFAULT_BACKEND_PORT})"
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=DEFAULT_FRONTEND_PORT,
        help=f"Custom frontend port (default: {DEFAULT_FRONTEND_PORT})"
    )
    
    args = parser.parse_args()
    
    backend_port = args.backend_port
    frontend_port = args.frontend_port
    no_ngrok = args.no_ngrok

    # Essential: Tell the frontend where the backend is
    os.environ["API_BASE_URL"] = f"http://localhost:{backend_port}/api/v1"
    
    log("\n" + "="*60)
    log("🚀 Multi-Agent-Auditor - Starting Production Instance...")
    log(f"   Backend Port:  {backend_port}")
    log(f"   Frontend Port: {frontend_port}")
    log(f"   Ngrok:         {'DISABLED' if no_ngrok else 'ENABLED'}")
    log("="*60)
    
    # Start Backend
    backend_proc = run_backend(backend_port)
    
    # Start Frontend
    frontend_proc = run_frontend(frontend_port)
    
    # Start ngrok if requested
    public_url = None
    if not no_ngrok:
        public_url = create_tunnels(frontend_port)
    
    log("\n" + "="*60)
    log(f"🏠 Local Backend URL:  http://localhost:{backend_port}")
    log(f"🏠 Local Frontend URL: http://localhost:{frontend_port}")
    log("="*60)
    log("\nPress Ctrl+C to stop.\n")
    
    try:
        # Wait for processes
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        log("\n🛑 Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        if not no_ngrok:
            safely_end_ngrok()
        log("👋 Goodbye!")
