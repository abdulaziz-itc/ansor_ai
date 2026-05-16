import os
import sys
import traceback
import logging
import warnings

# Silence all initialization stdout/stderr warnings preventing Passenger bootstrap failures
warnings.simplefilter("ignore")

# 1. ENVIROMENT FIX
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# 2. SETUP PATHS
USERNAME = "joidauz"
DOMAIN = "ansor.joida.uz"
BASE_DIR = f"/home/{USERNAME}/{DOMAIN}/backend"
PYTHON_VERSION = "3.11"

VENV_PATH_LIB = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib/python{PYTHON_VERSION}/site-packages"
VENV_PATH_LIB64 = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib64/python{PYTHON_VERSION}/site-packages"

# Add paths to sys.path
for path in [VENV_PATH_LIB, VENV_PATH_LIB64, BASE_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# 3. LOGGING FOR STARTUP ERRORS
logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'startup_error.log'),
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# 4. MAIN APPLICATION
def application(environ, start_response):
    try:
        from a2wsgi import ASGIMiddleware
        from app.main import app
        
        # Wrap FastAPI ASGI app to WSGI
        real_app = ASGIMiddleware(app)
        # CRITICAL: consume the iterator INSIDE try/except
        # so any async exceptions are caught here, not by Passenger
        result = real_app(environ, start_response)
        return list(result)
        
    except Exception:
        # Log the error to a file
        error_info = traceback.format_exc()
        logging.error(f"Backend Startup Error:\n{error_info}")
        
        # Diagnostic Mode for Browser
        status = '200 OK'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        html = f"""
        <html>
        <head>
            <title>Ansor AI - Startup Error</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; background: #0f172a; color: #f1f5f9; }}
                .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-top: 5px solid #ef4444; }}
                h1 {{ color: #ef4444; margin-top: 0; }}
                pre {{ background: #020617; padding: 20px; border-radius: 8px; color: #fca5a5; overflow-x: auto; border: 1px solid #334155; font-size: 14px; line-height: 1.5; }}
                .info {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Backend Startup Error</h1>
                <p class="info">Python: {sys.version} | Base: {BASE_DIR}</p>
                <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;"/>
                <p>Serverni ishga tushirishda xatolik yuz berdi. Batafsil ma'lumot:</p>
                <pre>{error_info}</pre>
                <p style="font-size: 12px; color: #64748b;">Xatolik <code>startup_error.log</code> fayliga ham yozildi.</p>
            </div>
        </body>
        </html>
        """
        return [html.encode('utf-8')]
