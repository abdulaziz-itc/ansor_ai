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
        # Log the error to a file using raw I/O (logging may be misconfigured)
        error_info = traceback.format_exc()
        try:
            debug_file = os.path.join(BASE_DIR, 'error_debug.txt')
            with open(debug_file, 'w') as f:
                f.write(error_info)
        except Exception:
            pass
        
        # Use WSGI exc_info protocol - works even if start_response was already called
        import sys
        import json
        try:
            start_response(
                '500 Internal Server Error',
                [('Content-Type', 'application/json; charset=utf-8')],
                sys.exc_info()
            )
            return [json.dumps({"detail": error_info}).encode('utf-8')]
        except Exception:
            # If we can't even send an error response, log and re-raise
            try:
                with open(os.path.join(BASE_DIR, 'critical_error.txt'), 'w') as f:
                    f.write(traceback.format_exc())
            except Exception:
                pass
            raise
