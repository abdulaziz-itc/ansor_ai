import os
import sys
import traceback

# EXACTLY DUPLICATE passenger_wsgi setup logic to see why it crashes there!
USERNAME = "joidauz"
DOMAIN = "ansor.joida.uz"
BASE_DIR = f"/home/{USERNAME}/{DOMAIN}/backend"
PYTHON_VERSION = "3.11"

VENV_PATH_LIB = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib/python{PYTHON_VERSION}/site-packages"
VENV_PATH_LIB64 = f"/home/{USERNAME}/virtualenv/{DOMAIN}/backend/{PYTHON_VERSION}/lib64/python{PYTHON_VERSION}/site-packages"

# Add paths to sys.path
print("1. Modifying sys.path like Passenger does...")
for path in [VENV_PATH_LIB, VENV_PATH_LIB64, BASE_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        print(f"   Added path: {path}")

print("\n2. Attempting to load key dependencies...")
try:
    import a2wsgi
    print("   ✅ a2wsgi imported.")
except Exception as e:
    print(f"   ❌ a2wsgi import FAILED: {e}")

try:
    import sqlalchemy
    print(f"   ✅ sqlalchemy imported (Version: {sqlalchemy.__version__}).")
except Exception as e:
    print(f"   ❌ sqlalchemy import FAILED: {e}")

try:
    import aiosqlite
    print("   ✅ aiosqlite imported.")
except Exception as e:
    print(f"   ❌ aiosqlite import FAILED: {e}")

print("\n3. Attempting to IMPORT the FastAPI app (THIS USUALLY REVEALS THE CRASH)...")
try:
    from app.main import app
    print("   ✅ APP LOADED SUCCESSFULLY!")
    print("   All internal initialization completed.")
except Exception as e:
    print("\n❌ APP CRASHED DURING IMPORT!! EXCEPTION DETAILS:")
    print("-" * 50)
    traceback.print_exc()
    print("-" * 50)
    print(f"Exception details: {e}")
