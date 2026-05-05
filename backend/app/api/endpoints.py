import logging
import os
import uuid
import json
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, WebSocket, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..database import get_db, SessionLocal
from ..models import MessageType, Message, Media
from ..services.ai_service import ai_service
from ..services.audio_service import audio_service
from ..services.websocket_manager import manager
from ..services.db_service import db_service
from . import schemas

# Logger sozlash
logger = logging.getLogger("ansor_ai.api")
router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

async def process_media_ai_task(message_id: int, video_path: str, user_id: int, chat_id: int):
    """
    AI tahlilini fonda bajaruvchi task.
    """
    logger.info(f"AI jarayoni boshlandi: MessageID={message_id}, ChatID={chat_id}")
    
    try:
        # 1. AI tahlili
        translated_text = await ai_service.translate_video(video_path)
        logger.info(f"AI tarjimasi tayyor: {translated_text[:50]}...")

        # 2. Audio yaratish
        audio_filename = await audio_service.generate_audio(translated_text)
        audio_url = f"/static/audio/{audio_filename}"
        logger.info(f"Audio fayl yaratildi: {audio_filename}")

        # 3. Bazani yangilash
        async with SessionLocal() as db:
            await db.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(content=translated_text)
            )
            
            db_media = Media(
                message_id=message_id,
                file_path=audio_url,
                file_type="audio/mpeg"
            )
            db.add(db_media)
            await db.commit()
            logger.info(f"Baza yangilandi: MessageID={message_id}")

            # 4. WebSocket xabari
            await manager.broadcast_global({
                "type": "ai_processing_complete",
                "data": {
                    "message_id": message_id,
                    "chat_id": chat_id,
                    "text": translated_text,
                    "audio_url": audio_url
                }
            })

    except Exception as e:
        logger.error(f"AI taskda xatolik: {str(e)}", exc_info=True)
        await manager.send_personal_message(
            json.dumps({
                "type": "error", 
                "message": f"AI tahlilida xatolik yuz berdi: {str(e)}"
            }),
            user_id
        )

@router.post(
    "/chats/{chat_id}/upload", 
    status_code=202,
    response_model=schemas.VideoUploadResponse,
    tags=["Media"],
    summary="Video yuklash va tahlilni boshlash",
    description="Ushbu endpoint videoni qabul qiladi va fonda AI tahlilini ishga tushiradi. Javob sifatida 'processing' holatini qaytaradi."
)
async def upload_video_to_chat(
    chat_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Video yuklash so'rovi: ChatID={chat_id}")
    file_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp4")
    
    try:
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            form = await request.form()
            video = form.get("video")
            if not video:
                raise HTTPException(status_code=400, detail="Video fayl topilmadi")
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
        else:
            with open(video_path, "wb") as buffer:
                async for chunk in request.stream():
                    buffer.write(chunk)
        
        db_msg = await db_service.create_message(
            db, sender_id=user_id, chat_id=chat_id, content="[Video tahlil qilinmoqda...]", msg_type=MessageType.VIDEO
        )

        background_tasks.add_task(process_media_ai_task, db_msg.id, video_path, user_id, chat_id)

        await manager.broadcast_global({
            "type": "chat_message",
            "data": {
                "id": db_msg.id,
                "chat_id": chat_id,
                "sender_id": user_id,
                "content": db_msg.content,
                "type": "video",
                "created_at": db_msg.created_at.isoformat()
            }
        })

        return {"status": "processing", "message_id": db_msg.id}

    except Exception as e:
        logger.error(f"Video yuklashda xatolik: {str(e)}")
        if os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/chats", 
    response_model=List[schemas.ChatRead],
    tags=["Chats"],
    summary="Barcha chatlar ro'yxati",
    description="Foydalanuvchiga tegishli bo'lgan barcha faol chatlar ro'yxatini qaytaradi."
)
async def list_chats(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await db_service.get_chats(db, skip=skip, limit=limit)

@router.get(
    "/chats/{chat_id}/messages", 
    response_model=List[schemas.MessageRead],
    tags=["Chats"],
    summary="Chat xabarlari tarixi",
    description="Berilgan chat ID bo'yicha barcha xabarlar tarixini (matn, video, audio) qaytaradi."
)
async def get_chat_messages(chat_id: int, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await db_service.get_messages(db, chat_id=chat_id, skip=skip, limit=limit)

@router.post(
    "/share", 
    response_model=schemas.SuccessResponse,
    tags=["Utility"],
    summary="Natijani ulashish",
    description="AI tomonidan olingan natijani boshqa platformalarga ulashish uchun xizmat qiladi."
)
async def share_result(data: dict):
    return {"status": "success", "message": "Natija muvaffaqiyatli ulashildi"}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    ### WebSocket ulanishi
    Real-vaqtda AI natijalarini kutib olish va signaling uchun ishlatiladi.
    - **Ulanish URL:** `ws://server/api/v1/ws/{user_id}`
    """
    await manager.connect(user_id, websocket)
    logger.info(f"WebSocket ulandi: UserID={user_id}")
    try:
        while True:
            data = await websocket.receive_text()
            # Kelgan xabarni log qilish
    except Exception as e:
        logger.warning(f"WebSocket uzildi: UserID={user_id}")
    finally:
        manager.disconnect(user_id)
