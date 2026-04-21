import sys
import os
import traceback

# 1. Setup paths
# NOTE: Replace 'joidauz' with your actual cPanel username if different
USERNAME = "joidauz"
DOMAIN = "ansor.joida.uz"
BASE_DIR = f"/home/{USERNAME}/{DOMAIN}/backend"
PYTHON_VERSION = "3.11" # Change this if you select a different version in cPanel

# Path to your virtual environment site-packages
# This will be created by cPanel "Setup Python App"
VENV_PATH = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib/python{PYTHON_VERSION}/site-packages"

if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. Main application entry point for Passenger
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
            <p><strong>Path Check:</strong> {BASE_DIR}</p>
            <hr/>
            <pre style="background: #000; padding: 15px; border-radius: 5px; overflow-x: auto;">{error_info}</pre>
        </body>
        </html>
        """
        return [html.encode('utf-8')]
