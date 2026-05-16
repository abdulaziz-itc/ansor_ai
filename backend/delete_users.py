import asyncio
import os
import sys

# app modulini import qilish uchun path ga qo'shamiz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import delete
from app.database import SessionLocal
from app.models import User, Message

async def delete_test_users():
    # O'chirilishi kerak bo'lgan foydalanuvchilar ID lari
    user_ids_to_delete = [1, 2, 3, 4]
    
    async with SessionLocal() as session:
        try:
            # 1. Avval ushbu foydalanuvchilarga tegishli xabarlarni o'chiramiz (Foreign Key xatosi chiqmasligi uchun)
            msg_result = await session.execute(delete(Message).where(Message.sender_id.in_(user_ids_to_delete)))
            print(f"{msg_result.rowcount} ta tegishli xabar o'chirildi.")
            
            # 2. Keyin foydalanuvchilarning o'zini o'chiramiz
            user_result = await session.execute(delete(User).where(User.id.in_(user_ids_to_delete)))
            print(f"{user_result.rowcount} ta foydalanuvchi o'chirildi.")
            
            # O'zgarishlarni saqlash
            await session.commit()
            print("Muvaffaqiyatli yakunlandi!")
            
        except Exception as e:
            await session.rollback()
            print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(delete_test_users())
