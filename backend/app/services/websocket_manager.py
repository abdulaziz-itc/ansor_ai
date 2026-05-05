import json
import logging
from typing import Dict, List, Optional
from fastapi import WebSocket

# Logger sozlash
logger = logging.getLogger("ansor_ai.websocket")

class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket ulanishi
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Yangi foydalanuvchini WebSocket orqali ulash."""
        await websocket.accept()
        # Agar oldindan ulanish bo'lsa, uni yopamiz (duplicate ulanishlarni oldini olish)
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
        
        self.active_connections[user_id] = websocket
        logger.info(f"Foydalanuvchi ulandi: UserID={user_id}. Jami ulanishlar: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        """Foydalanuvchi ulanishini o'chirish."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"Foydalanuvchi uzildi: UserID={user_id}. Qolgan ulanishlar: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, user_id: int):
        """Faqat bitta foydalanuvchiga xabar yuborish."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Xabar yuborishda xatolik (UserID={user_id}): {str(e)}")
                self.disconnect(user_id)

    async def broadcast_global(self, message: dict):
        """Barcha ulangan foydalanuvchilarga xabar yuborish."""
        message_json = json.dumps(message)
        logger.debug(f"Global broadcast: {message['type']}")
        
        # Ulanishlar ro'yxatidan nusxa olamiz (iteratsiya vaqtida o'zgarmasligi uchun)
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Broadcast xatosi (UserID={user_id}): {str(e)}")
                disconnected_users.append(user_id)
        
        # Uzilgan foydalanuvchilarni tozalash
        for user_id in disconnected_users:
            self.disconnect(user_id)

    async def broadcast_to_chat_members(self, message: dict, members: List[int]):
        """Faqat ma'lum bir chat a'zolariga xabar yuborish."""
        message_json = json.dumps(message)
        for user_id in members:
            await self.send_personal_message(message_json, user_id)

manager = ConnectionManager()
