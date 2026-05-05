from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..models import User, Chat, Message, Media, MessageType
from ..api import schemas
from typing import List

class DBService:
    async def get_chats(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Chat]:
        result = await db.execute(select(Chat).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_messages(self, db: AsyncSession, chat_id: int, skip: int = 0, limit: int = 50) -> List[Message]:
        query = select(Message).where(Message.chat_id == chat_id).order_by(desc(Message.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        # Return in chronological order for the client
        messages = result.scalars().all()
        return messages[::-1]

    async def create_message(self, db: AsyncSession, sender_id: int, chat_id: int, content: str, msg_type: MessageType = MessageType.TEXT) -> Message:
        db_msg = Message(
            sender_id=sender_id,
            chat_id=chat_id,
            content=content,
            type=msg_type
        )
        db.add(db_msg)
        await db.commit()
        await db.refresh(db_msg)
        return db_msg

db_service = DBService()
