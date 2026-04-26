import os
import sys
import traceback

# 1. ENVIROMENT FIX (MUST BE AT THE TOP)
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# 1.5 EXPLICITLY LOAD .ENV (Bulletproof method for cPanel)
env_file_path = "/home/joidauz/ansor.joida.uz/backend/.env"
if os.path.exists(env_file_path):
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# 2. SETUP PATHS
USERNAME = "joidauz"
DOMAIN = "ansor.joida.uz"
BASE_DIR = f"/home/{USERNAME}/{DOMAIN}/backend"
PYTHON_VERSION = "3.11"

# Path to your virtual environment site-packages (both lib and lib64)
VENV_PATH_LIB = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib/python{PYTHON_VERSION}/site-packages"
VENV_PATH_LIB64 = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib64/python{PYTHON_VERSION}/site-packages"

# Add paths to sys.path
for path in [VENV_PATH_LIB, VENV_PATH_LIB64, BASE_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# 3. MAIN APPLICATION
def application(environ, start_response):
    try:
        from a2wsgi import ASGIMiddleware
        from app.main import app
        
        # Wrap FastAPI ASGI app to WSGI
        real_app = ASGIMiddleware(app)
        return real_app(environ, start_response)
        
    except Exception:
        # Diagnostic Mode: Show startup errors in the browser
        error_info = traceback.format_exc()
        status = '200 OK'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        html = f"""
        <html>
        <head><title>Backend Startup Error</title></head>
        <body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #ff5555;">
            <h1 style="color: #ffffff;">Backend Startup Error (Diagnostic Mode)</h1>
            <hr/>
            <p><strong>Python Version:</strong> {sys.version}</p>
            <p><strong>Checking Paths:</strong></p>
            <ul>
                <li>LIB: {VENV_PATH_LIB} (Exists: {os.path.exists(VENV_PATH_LIB)})</li>
                <li>LIB64: {VENV_PATH_LIB64} (Exists: {os.path.exists(VENV_PATH_LIB64)})</li>
                <li>BASE: {BASE_DIR} (Exists: {os.path.exists(BASE_DIR)})</li>
            </ul>
            <hr/>
            <pre style="background: #000; padding: 15px; border-radius: 5px; overflow-x: auto;">{error_info}</pre>
        </body>
        </html>
        """
        return [html.encode('utf-8')]
