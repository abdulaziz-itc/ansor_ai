import asyncio
import sys
import os

# Import internal components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.database import SessionLocal
    from app.services.db_service import db_service
    from app.api import schemas
    from app.services.auth_service import auth_service
    print("✅ Imports completed successfully.")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_registration():
    print("Testing user registration logic flow simulation...")
    
    async with SessionLocal() as session:
        try:
            # Mock payload
            user_create = schemas.UserCreate(
                username="test_debug_user",
                full_name="Test User",
                email="debug_test@example.com",
                password="password123"
            )
            
            print("1. Attempting get_user_by_username...")
            db_user = await db_service.get_user_by_username(session, user_create.username)
            print(f"   Result: {db_user}")

            print("2. Attempting get_user_by_email...")
            db_email = await db_service.get_user_by_email(session, user_create.email)
            print(f"   Result: {db_email}")

            print("3. Attempting password hash...")
            hashed = auth_service.get_password_hash("password123")
            print(f"   Hash success: {hashed[:10]}...")
            
            print("4. Attempting User instance generation and database commit...")
            user = await db_service.create_user(session, user_create, hashed)
            
            print(f"🎉 SIMULATION COMPLETED! Successfully created user ID: {user.id}")
            print("If this completed here but fails on the web, check server proxy file permissions.")
            
        except Exception as e:
            import traceback
            print("\n❌ SIMULATION FAILED! CRASH DETECTED:")
            print("-" * 60)
            traceback.print_exc()
            print("-" * 60)
            print(f"Error string: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_registration())
