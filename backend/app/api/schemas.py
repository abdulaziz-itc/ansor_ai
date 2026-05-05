from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., example="ali_valiyev", description="Foydalanuvchi nomi")
    email: EmailStr = Field(..., example="ali@example.com", description="Elektron pochta manzili")

class UserCreate(UserBase):
    password: str = Field(..., example="strong_password123", description="Maxfiy parol")

class UserRead(UserBase):
    id: int = Field(..., example=1)
    created_at: datetime

    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    content: Optional[str] = Field(None, example="Salom, qandaysiz?", description="Xabar matni")
    type: MessageType = Field(MessageType.TEXT, example="text", description="Xabar turi (text, video, audio)")

class MessageCreate(MessageBase):
    chat_id: int = Field(..., example=1, description="Chat ID")

class MessageRead(MessageBase):
    id: int = Field(..., example=101)
    chat_id: int = Field(..., example=1)
    sender_id: int = Field(..., example=1)
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Schemas
class ChatBase(BaseModel):
    name: Optional[str] = Field(None, example="Umumiy guruh", description="Chat nomi")

class ChatCreate(ChatBase):
    pass

class ChatRead(ChatBase):
    id: int = Field(..., example=1)
    created_at: datetime
    
    class Config:
        from_attributes = True

# Response Schemas for Swagger
class VideoUploadResponse(BaseModel):
    status: str = Field(..., example="processing", description="Jarayon holati")
    message_id: int = Field(..., example=101, description="Yaratilgan xabar IDsi")

class SuccessResponse(BaseModel):
    status: str = Field(..., example="success")
    message: str = Field(..., example="Amal muvaffaqiyatli bajarildi")

# WebSocket Message Structure
class WSMessage(BaseModel):
    type: str = Field(..., example="ai_processing_complete", description="Xabar turi")
    data: dict = Field(..., description="Xabar ma'lumotlari")
