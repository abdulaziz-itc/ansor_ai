from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    content: Optional[str] = None
    type: MessageType = MessageType.TEXT

class MessageCreate(MessageBase):
    chat_id: int

class MessageRead(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Schemas
class ChatBase(BaseModel):
    name: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class ChatRead(ChatBase):
    id: int
    created_at: datetime
    # Optionally include last message
    
    class Config:
        from_attributes = True

# WebSocket Message Structure
class WSMessage(BaseModel):
    type: str # "chat_message", "notification", etc.
    data: dict
