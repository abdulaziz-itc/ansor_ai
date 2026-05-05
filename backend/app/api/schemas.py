from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    CALL = "call"

class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., example="macbook13")
    full_name: Optional[str] = Field(None, example="Abdurahmon")
    email: EmailStr = Field(..., example="user@example.com")
    avatar_url: Optional[str] = Field(None, example="https://ansor.joida.uz/static/avatars/default.png")

class UserCreate(UserBase):
    password: str = Field(..., example="password123")

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, example="Abdurahmon Yangilangan")
    avatar_url: Optional[str] = Field(None, example="https://ansor.joida.uz/static/avatars/new.png")
    email: Optional[EmailStr] = Field(None, example="new_email@example.com")

class UserRead(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Media/File Schemas
class MediaRead(BaseModel):
    file_path: str
    file_type: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    content: Optional[str] = None
    type: MessageType = MessageType.TEXT
    metadata_json: Optional[Dict[str, Any]] = None

class MessageRead(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    created_at: datetime
    media: Optional[MediaRead] = None
    class Config:
        from_attributes = True

# Chat Schemas
class ChatRead(BaseModel):
    id: int
    name: Optional[str] = None
    type: ChatType
    created_at: datetime
    class Config:
        from_attributes = True
# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Call Signaling Schema
class SignalData(BaseModel):
    target_id: int = Field(..., description="Signal yuborilayotgan foydalanuvchi IDsi")
    type: str = Field(..., example="offer", description="Signal turi (offer, answer, candidate)")
    signal: Dict[str, Any] = Field(..., description="SDP yoki ICE candidate ma'lumotlari")
