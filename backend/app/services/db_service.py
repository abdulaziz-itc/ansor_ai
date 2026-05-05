import logging
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from ..models import User, Chat, Message, Media, MessageType, ChatType

logger = logging.getLogger("ansor_ai.db_service")

class DBService:
    async def get_chats(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Chat]:
        result = await db.execute(
            select(Chat).order_by(desc(Chat.created_at)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_chat(self, db: AsyncSession, name: Optional[str] = None, chat_type: ChatType = ChatType.PRIVATE) -> Chat:
        db_chat = Chat(name=name, type=chat_type)
        db.add(db_chat)
        await db.commit()
        await db.refresh(db_chat)
        logger.info(f"Chat yaratildi: ID={db_chat.id}, Type={chat_type}")
        return db_chat

    async def get_messages(self, db: AsyncSession, chat_id: int, skip: int = 0, limit: int = 50) -> List[Message]:
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .options(selectinload(Message.media))
            .order_by(desc(Message.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        messages = result.scalars().all()
        return messages[::-1]

    async def create_message(
        self, 
        db: AsyncSession, 
        sender_id: int, 
        chat_id: int, 
        content: str, 
        msg_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        db_msg = Message(
            sender_id=sender_id,
            chat_id=chat_id,
            content=content,
            type=msg_type,
            metadata_json=metadata
        )
        db.add(db_msg)
        await db.commit()
        await db.refresh(db_msg)
        return db_msg

    async def add_media(
        self, 
        db: AsyncSession, 
        message_id: int, 
        file_path: str, 
        file_type: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> Media:
        db_media = Media(
            message_id=message_id,
            file_path=file_path,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size
        )
        db.add(db_media)
        await db.commit()
        await db.refresh(db_media)
        return db_media

db_service = DBService()
