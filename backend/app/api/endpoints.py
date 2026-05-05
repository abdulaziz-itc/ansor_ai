import logging
import os
import uuid
import json
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, WebSocket, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..database import get_db, SessionLocal
from ..models import MessageType, Message, Media, ChatType
from ..services.ai_service import ai_service
from ..services.audio_service import audio_service
from ..services.websocket_manager import manager
from ..services.db_service import db_service
from . import schemas
from .deps import get_current_user
from ..models import User

logger = logging.getLogger("ansor_ai.api")
router = APIRouter()

# Fayllarni saqlash uchun papkalar
UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
STICKERS_DIR = os.path.join(UPLOAD_DIR, "stickers")

for d in [UPLOAD_DIR, FILES_DIR, STICKERS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# --- Chat Endpointlari ---

@router.post("/chats", response_model=schemas.ChatRead, tags=["Chats"], summary="Yangi chat yaratish")
async def create_chat(
    name: Optional[str] = None, 
    type: ChatType = ChatType.PRIVATE, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Shaxsiy yoki guruh chatini yaratish."""
    return await db_service.create_chat(db, name=name, chat_type=type)

@router.get("/chats", response_model=List[schemas.ChatRead], tags=["Chats"])
async def list_chats(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await db_service.get_chats(db, skip=skip, limit=limit)

@router.get("/chats/{chat_id}/messages", response_model=List[schemas.MessageRead], tags=["Chats"])
async def get_chat_messages(
    chat_id: int, 
    skip: int = 0, 
    limit: int = 50, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await db_service.get_messages(db, chat_id=chat_id, skip=skip, limit=limit)

# --- Media va Fayllar ---

@router.post("/chats/{chat_id}/upload-file", tags=["Media"], summary="Fayl yuklash (Hujjat, Rasm, Stiker)")
async def upload_file(
    chat_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Telegram kabi har qanday faylni chatga yuborish."""
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{ext}"
    filepath = os.path.join(FILES_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Baza yozuvi
    db_msg = await db_service.create_message(
        db, sender_id=current_user.id, chat_id=chat_id, content=file.filename, msg_type=MessageType.FILE
    )
    
    await db_service.add_media(
        db, message_id=db_msg.id, file_path=f"/uploads/files/{filename}", 
        file_type=file.content_type, file_name=file.filename
    )
    
    # WebSocket orqali xabar
    await manager.broadcast_global({
        "type": "chat_message",
        "data": {
            "id": db_msg.id,
            "chat_id": chat_id,
            "type": "file",
            "content": file.filename,
            "file_url": f"/uploads/files/{filename}"
        }
    })
    
    return {"status": "success", "message_id": db_msg.id}

# --- AI Video Processing (Mavjud funksiya) ---

@router.post("/chats/{chat_id}/upload-video", status_code=202, tags=["Media"])
async def upload_video(
    chat_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Videoni qabul qilish va AI tahlilini navbatga qo'yish."""
    file_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp4")
    
    # Binary yoki Multipart qabul qilish
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        video = form.get("video")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
    else:
        with open(video_path, "wb") as buffer:
            async for chunk in request.stream():
                buffer.write(chunk)
    
    from .endpoints import process_media_ai_task # Cyclic import oldini olish uchun
    db_msg = await db_service.create_message(
        db, sender_id=current_user.id, chat_id=chat_id, content="[Video tahlili...]", msg_type=MessageType.VIDEO
    )
    
    background_tasks.add_task(process_media_ai_task, db_msg.id, video_path, current_user.id, chat_id)
    return {"status": "processing", "message_id": db_msg.id}

# --- WebSocket & WebRTC Signaling ---

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebRTC Signaling va Real-vaqtda xabarlar."""
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            msg_type = message_data.get("type")
            
            # 1. Oddiy matnli xabar
            if msg_type == "chat_message":
                payload = message_data.get("data", {})
                async with SessionLocal() as db:
                    db_msg = await db_service.create_message(
                        db, sender_id=user_id, chat_id=payload['chat_id'], content=payload['content']
                    )
                    await manager.broadcast_global({
                        "type": "chat_message",
                        "data": {
                            "id": db_msg.id,
                            "chat_id": db_msg.chat_id,
                            "content": db_msg.content,
                            "sender_id": user_id
                        }
                    })

            # 2. WebRTC Signal (Offer/Answer/Candidate)
            elif msg_type == "signal":
                payload = message_data.get("data", {})
                target_id = payload.get("target_id")
                if target_id:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "signal",
                            "data": {
                                "from_id": user_id,
                                "type": payload.get("type"),
                                "signal": payload.get("signal")
                            }
                        }),
                        target_id
                    )

            # 3. Qo'ng'iroq boshlash (Call Start)
            elif msg_type == "call_invite":
                payload = message_data.get("data", {})
                target_id = payload.get("target_id")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "call_invite",
                        "data": {
                            "from_id": user_id,
                            "chat_id": payload.get("chat_id"),
                            "is_video": payload.get("is_video", True)
                        }
                    }),
                    target_id
                )

    except Exception as e:
        logger.warning(f"WebSocket uzildi (UserID={user_id}): {e}")
    finally:
        manager.disconnect(user_id)

# Background task logic (endpoints.py oxirida yoki alohida faylda)
async def process_media_ai_task(message_id: int, video_path: str, user_id: int, chat_id: int):
    from ..services.ai_service import ai_service
    from ..services.audio_service import audio_service
    try:
        text = await ai_service.translate_video(video_path)
        audio_file = await audio_service.generate_audio(text)
        async with SessionLocal() as db:
            await db.execute(update(Message).where(Message.id == message_id).values(content=text))
            await db_service.add_media(db, message_id, f"/static/audio/{audio_file}", "audio/mpeg")
            await db.commit()
            await manager.broadcast_global({
                "type": "ai_processing_complete",
                "data": {"message_id": message_id, "chat_id": chat_id, "text": text, "audio_url": f"/static/audio/{audio_file}"}
            })
    except Exception as e:
        logger.error(f"AI Task xatosi: {e}")
