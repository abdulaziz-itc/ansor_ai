import json
import logging
from typing import Dict, List, Set, Optional
from fastapi import WebSocket

logger = logging.getLogger("ansor_ai.websocket")

class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket ulanishi
        self.active_connections: Dict[int, WebSocket] = {}
        # Online foydalanuvchilar to'plami
        self.online_users: Set[int] = set()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.online_users.add(user_id)
        
        # Foydalanuvchi online bo'lganini hammaga bildirish
        await self.broadcast_global({
            "type": "user_status",
            "data": {"user_id": user_id, "status": "online"}
        })
        logger.info(f"Foydalanuvchi online: UserID={user_id}")

    async def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.online_users:
            self.online_users.remove(user_id)
            
        # Foydalanuvchi offline bo'lganini bildirish
        await self.broadcast_global({
            "type": "user_status",
            "data": {"user_id": user_id, "status": "offline"}
        })
        logger.info(f"Foydalanuvchi offline: UserID={user_id}")

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except:
                await self.disconnect(user_id)

    async def broadcast_global(self, message: dict):
        message_json = json.dumps(message)
        for user_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[user_id].send_text(message_json)
            except:
                await self.disconnect(user_id)

manager = ConnectionManager()
