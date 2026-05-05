from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class MessageType(enum.Enum):
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="sender")
    # Chats are many-to-many, but for simplicity let's start with a link or just direct messages
    # We'll use a many-to-many through a helper table for real group chats later if needed.

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=True)
    type = Column(Enum(MessageType), default=MessageType.TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    media = relationship("Media", back_populates="message", uselist=False)

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # e.g. "video/mp4"
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="media")
