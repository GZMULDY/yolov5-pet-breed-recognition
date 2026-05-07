"""
One-click startup script for the pet breed recognition system.
Starts both FastAPI backend and Vue 3 frontend simultaneously.
Usage: python start.py
"""
import subprocess
import sys
import os
import signal
import time
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(BASE_DIR, "system", "back")
FRONTEND_DIR = os.path.join(BASE_DIR, "system", "pre")

CONDA_ENV = "yolo"
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

processes = []


def _is_port_in_use(port):
    """Check if a port is currently in use."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', port))
        s.close()
        return False
    except OSError:
        return True


def _kill_port(port):
    """Kill any process holding the given port on Windows."""
    if not _is_port_in_use(port):
        return
    print(f"  Cleaning up stale process on port {port}...")
    try:
        result = subprocess.run(
            ['cmd', '/c', f'netstat -ano | findstr :{port} | findstr LISTENING'],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if parts:
                pid = parts[-1]
                subprocess.run(['cmd', '/c', f'taskkill /F /PID {pid}'],
                               capture_output=True)
    except Exception:
        pass


def start_backend():
    """Start FastAPI backend with uvicorn."""
    python_exe = sys.executable
    backend_cmd = [
        python_exe, '-m', 'uvicorn', 'main:app',
        '--host', BACKEND_HOST, '--port', str(BACKEND_PORT),
        '--reload'
    ]
    proc = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    processes.append(("Backend", proc))
    print(f"  [Backend] Started on http://{BACKEND_HOST}:{BACKEND_PORT}")


def start_frontend():
    """Start Vue 3 frontend dev server."""
    frontend_cmd = f'cd /d "{FRONTEND_DIR}" && npm run dev'
    proc = subprocess.Popen(
        frontend_cmd,
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    processes.append(("Frontend", proc))
    print(f"  [Frontend] Started (Vite dev server)")


def cleanup(signum=None, frame=None):
    """Terminate all child processes on exit."""
    print("\n  Shutting down...")
    for name, proc in processes:
        if proc.poll() is None:
            print(f"  Stopping {name} (PID {proc.pid})...")
            proc.terminate()
    # Give processes a moment to terminate gracefully
    time.sleep(2)
    for name, proc in processes:
        if proc.poll() is None:
            print(f"  Force killing {name} (PID {proc.pid})...")
            proc.kill()
    print("  All services stopped.")


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    print("=" * 50)
    print("  Pet Breed Recognition System - Starting All Services")
    print("=" * 50)

    # Clean up stale processes from previous runs
    _kill_port(BACKEND_PORT)
    for p in range(FRONTEND_PORT, FRONTEND_PORT + 3):
        _kill_port(p)

    print("\n[1/2] Starting Backend (FastAPI)...")
    start_backend()

    print("\n[2/2] Starting Frontend (Vue 3 + Vite)...")
    start_frontend()

    print("\n" + "=" * 50)
    print("  All services are running. Press Ctrl+C to stop.")
    print(f"  Backend API:  http://{BACKEND_HOST}:{BACKEND_PORT}/api/v1")
    print("  Swagger Docs: http://localhost:8000/docs")
    print("=" * 50 + "\n")

    # Wait for child processes
    try:
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n  [ERROR] {name} exited unexpectedly (code {proc.returncode}).")
                    cleanup()
                    sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
