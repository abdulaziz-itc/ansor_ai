from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # Maps user_id to their active WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected")

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def broadcast_to_users(self, message: dict, user_ids: List[int]):
        """
        Sends a message to a specific list of users (e.g., members of a chat).
        """
        message_json = json.dumps(message)
        for user_id in user_ids:
            if user_id in self.active_connections:
                await self.active_connections[user_id].send_text(message_json)

    async def broadcast_global(self, message: dict):
        """
        Sends a message to ALL connected users.
        """
        message_json = json.dumps(message)
        for connection in self.active_connections.values():
            await connection.send_text(message_json)

manager = ConnectionManager()
