import os
import sys
import json
import traceback
import warnings

warnings.simplefilter("ignore")

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

USERNAME = "joidauz"
DOMAIN = "ansor.joida.uz"
BASE_DIR = f"/home/{USERNAME}/{DOMAIN}/backend"
PYTHON_VERSION = "3.11"

VENV_PATH_LIB = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib/python{PYTHON_VERSION}/site-packages"
VENV_PATH_LIB64 = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib64/python{PYTHON_VERSION}/site-packages"

for path in [VENV_PATH_LIB, VENV_PATH_LIB64, BASE_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

try:
    with open(os.path.join(BASE_DIR, 'module_loaded.txt'), 'w') as _f:
        _f.write(f"Module loaded. Python: {sys.version}\n")
except Exception:
    pass

# HTTP status phrase map (minimal)
HTTP_PHRASES = {
    200: "OK", 201: "Created", 204: "No Content",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not Found", 422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def _run_asgi(app, environ, start_response):
    """Custom ASGI→WSGI bridge using asyncio. Handles response lifecycle cleanly."""
    import asyncio

    response_status = [None]
    response_headers = [None]
    response_body = []
    response_started = [False]

    # Read request body
    try:
        content_length = int(environ.get('CONTENT_LENGTH') or 0)
        body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''
    except Exception:
        body = b''

    # Build ASGI scope
    path = environ.get('PATH_INFO', '/')
    query = environ.get('QUERY_STRING', '').encode('latin1')
    method = environ.get('REQUEST_METHOD', 'GET')
    server_name = environ.get('SERVER_NAME', 'localhost')
    server_port = int(environ.get('SERVER_PORT', 80))

    # Build headers
    headers = []
    for key, val in environ.items():
        if key.startswith('HTTP_'):
            name = key[5:].lower().replace('_', '-').encode('latin1')
            headers.append((name, val.encode('latin1')))
        elif key == 'CONTENT_TYPE' and val:
            headers.append((b'content-type', val.encode('latin1')))
        elif key == 'CONTENT_LENGTH' and val:
            headers.append((b'content-length', val.encode('latin1')))

    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': method,
        'headers': headers,
        'path': path,
        'query_string': query,
        'root_path': '',
        'scheme': environ.get('wsgi.url_scheme', 'https'),
        'server': (server_name, server_port),
    }

    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}

    async def send(message):
        if message['type'] == 'http.response.start' and not response_started[0]:
            response_started[0] = True
            status_code = message['status']
            phrase = HTTP_PHRASES.get(status_code, 'Unknown')
            response_status[0] = f"{status_code} {phrase}"
            response_headers[0] = [
                (k.decode('latin1'), v.decode('latin1'))
                for k, v in message.get('headers', [])
            ]
        elif message['type'] == 'http.response.body' and response_started[0]:
            chunk = message.get('body', b'')
            if chunk:
                response_body.append(chunk)

    async def run_app():
        try:
            await app(scope, receive, send)
        except Exception:
            pass  # Swallow cleanup errors (e.g. session.close() failures)

    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_app())
    finally:
        try:
            loop.close()
        except Exception:
            pass

    if not response_started[0]:
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        return [b'{"detail": "ASGI app did not produce a response"}']

    start_response(response_status[0], response_headers[0])
    return response_body


def application(environ, start_response):
    try:
        from app.main import app
        return _run_asgi(app, environ, start_response)
    except Exception:
        exc_info = sys.exc_info()
        error_info = traceback.format_exc()
        try:
            with open(os.path.join(BASE_DIR, 'error_debug.txt'), 'w') as f:
                f.write(error_info)
        except Exception:
            pass
        try:
            start_response('500 Internal Server Error',
                           [('Content-Type', 'application/json')],
                           exc_info)
        except Exception:
            start_response('500 Internal Server Error',
                           [('Content-Type', 'application/json')])
        return [json.dumps({"detail": error_info}).encode()]
