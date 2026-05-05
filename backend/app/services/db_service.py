import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from ..models import User, Chat, Message, Media, MessageType

# Logger sozlash
logger = logging.getLogger("ansor_ai.db_service")

class DBService:
    async def get_chats(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Chat]:
        """Barcha chatlar ro'yxatini olish."""
        logger.debug(f"Chatlarni olish: skip={skip}, limit={limit}")
        result = await db.execute(
            select(Chat).order_by(desc(Chat.created_at)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_chat(self, db: AsyncSession, name: Optional[str] = None) -> Chat:
        """Yangi chat yaratish."""
        db_chat = Chat(name=name)
        db.add(db_chat)
        await db.commit()
        await db.refresh(db_chat)
        logger.info(f"Yangi chat yaratildi: ID={db_chat.id}")
        return db_chat

    async def get_messages(self, db: AsyncSession, chat_id: int, skip: int = 0, limit: int = 50) -> List[Message]:
        """Chat xabarlarini media ma'lumotlari bilan birga olish."""
        logger.debug(f"Xabarlarni olish: ChatID={chat_id}")
        
        # selectinload media ma'lumotlarini bitta so'rovda samarali yuklaydi
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
        # Foydalanuvchi interfeysi uchun vaqt bo'yicha to'g'ri tartibda (eskidan yangiga) qaytaramiz
        return messages[::-1]

    async def create_message(
        self, 
        db: AsyncSession, 
        sender_id: int, 
        chat_id: int, 
        content: str, 
        msg_type: MessageType = MessageType.TEXT
    ) -> Message:
        """Yangi xabar yaratish."""
        db_msg = Message(
            sender_id=sender_id,
            chat_id=chat_id,
            content=content,
            type=msg_type
        )
        db.add(db_msg)
        await db.commit()
        await db.refresh(db_msg)
        logger.info(f"Xabar yaratildi: ID={db_msg.id}, Type={msg_type}")
        return db_msg

    async def add_media_to_message(
        self, 
        db: AsyncSession, 
        message_id: int, 
        file_path: str, 
        file_type: str
    ) -> Media:
        """Xabarga media (audio/video) bog'lash."""
        db_media = Media(
            message_id=message_id,
            file_path=file_path,
            file_type=file_type
        )
        db.add(db_media)
        await db.commit()
        await db.refresh(db_media)
        logger.info(f"Media bog'landi: MessageID={message_id}, Path={file_path}")
        return db_media

db_service = DBService()
