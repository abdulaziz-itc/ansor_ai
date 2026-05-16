import asyncio
import os
import sys

# app modulini import qilish uchun path ga qo'shamiz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.database import SessionLocal
from app.models import User

async def list_users():
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Jami foydalanuvchilar: {len(users)}")
        print("-" * 50)
        for u in users:
            print(f"ID: {u.id:<3} | Username: {u.username:<15} | Email: {u.email:<25} | Name: {u.full_name}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(list_users())
