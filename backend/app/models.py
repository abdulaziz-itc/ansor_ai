import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from .database import Base

class MessageType(str, enum.Enum):
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    CALL = "call"

class ChatType(str, enum.Enum):
    PRIVATE = "private"
    GROUP = "group"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True) 
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="sender")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    type = Column(Enum(ChatType), default=ChatType.PRIVATE)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=True)
    type = Column(Enum(MessageType), default=MessageType.TEXT)
    metadata_json = Column(JSON, nullable=True) # Qo'shimcha ma'lumotlar (fayl nomi, call duration va h.k.)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    media = relationship("Media", back_populates="message", uselist=False)

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="media")
