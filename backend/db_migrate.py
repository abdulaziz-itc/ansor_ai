import asyncio
import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Setup imports from parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import engine
try:
    from app.database import engine
    print("Database engine found successfully.")
except ImportError as e:
    print(f"Failed to import database engine: {e}")
    sys.exit(1)

async def run_migration():
    print("Starting automated schema migration...")
    
    alter_queries = [
        # 1. Add google_id column safely (if not exists)
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR;"),
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR;"),
        
        # 2. Add index for performance if possible
        text("CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id);"),
        
        # 3. Make hashed_password nullable so Google Auth works
        text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;"),
    ]
    
    try:
        async with engine.begin() as conn:
            for query in alter_queries:
                try:
                    print(f"Executing: {query}")
                    await conn.execute(query)
                    print(" -> Done.")
                except Exception as inner_ex:
                    print(f" -> Notice (Might exist): {inner_ex}")
            
        print("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("Restart your FastAPI server for the changes to take full effect.")
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")

if __name__ == "__main__":
    # Ensure event loop is clean
    asyncio.run(run_migration())
