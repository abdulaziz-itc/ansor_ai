import os
import sys
import json
import traceback
import warnings

# Silence all initialization stdout/stderr warnings preventing Passenger bootstrap failures
warnings.simplefilter("ignore")

# 1. ENVIRONMENT FIX
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

# 3. MODULE-LEVEL DEBUG: confirm this file is being loaded by Passenger
try:
    with open(os.path.join(BASE_DIR, 'module_loaded.txt'), 'w') as _f:
        _f.write(f"passenger_wsgi.py loaded. Python: {sys.version}\nPaths: {sys.path[:5]}\n")
except Exception:
    pass


def _write_debug(filename, content):
    """Write debug info to a file safely."""
    try:
        with open(os.path.join(BASE_DIR, filename), 'w') as f:
            f.write(content)
    except Exception:
        pass


# 4. MAIN APPLICATION
def application(environ, start_response):
    # ENTRY DEBUG: confirm application() is being called
    _write_debug('request_debug.txt',
                 f"application() called\nPATH: {environ.get('PATH_INFO', '?')}\n"
                 f"METHOD: {environ.get('REQUEST_METHOD', '?')}\n")

    # Wrap start_response to detect if it's being called
    sr_log = []
    def wrapped_start_response(status, headers, exc_info=None):
        sr_log.append(status)
        _write_debug('start_response_debug.txt', f"start_response called with: {status}")
        if exc_info:
            return start_response(status, headers, exc_info)
        return start_response(status, headers)

    try:
        from a2wsgi import ASGIMiddleware
        from app.main import app

        _write_debug('import_ok.txt', "Imports succeeded")

        real_app = ASGIMiddleware(app)
        result = real_app(environ, wrapped_start_response)
        body = list(result)

        if not sr_log:
            # start_response was NEVER called - this causes "Server got itself in trouble"
            _write_debug('no_start_response.txt',
                        f"ERROR: start_response never called!\nbody chunks: {len(body)}\nbody: {body[:2]}")
            start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
            return [json.dumps({"detail": "ASGI app did not produce a response (startup failed?)"}).encode()]

        _write_debug('response_ok.txt', f"Response generated OK. status={sr_log[0]}, chunks={len(body)}")
        return body

    except Exception:
        # Capture exc_info IMMEDIATELY before any nested try/except clears it
        exc_info = sys.exc_info()
        error_info = traceback.format_exc()

        # Write error to file for diagnosis
        _write_debug('error_debug.txt', error_info)

        # Use proper WSGI exc_info protocol - safe even if start_response already called
        try:
            start_response(
                '500 Internal Server Error',
                [('Content-Type', 'application/json; charset=utf-8')],
                exc_info
            )
            return [json.dumps({"detail": error_info}).encode('utf-8')]
        except Exception:
            _write_debug('critical_error.txt', traceback.format_exc())
            # Return minimal response without changing headers
            return [json.dumps({"detail": "Critical server error"}).encode('utf-8')]
