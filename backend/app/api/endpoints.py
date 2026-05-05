from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import shutil
import os
import uuid
from ..services.ai_service import ai_service
from ..services.audio_service import audio_service
from fastapi import BackgroundTasks
from ..services.websocket_manager import manager
from ..services.db_service import db_service
from ..database import get_db
from ..models import MessageType
from . import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import json

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

async def process_media_ai(message_id: int, video_path: str, user_id: int, chat_id: int):
    """
    Background task to process video with Gemini and generate audio.
    """
    from ..database import SessionLocal
    from ..models import Media
    
    try:
        # 1. Translate video to text using AI
        translated_text = await ai_service.translate_video(video_path)
        
        # 2. Generate audio from text
        audio_filename = await audio_service.generate_audio(translated_text)
        audio_url = f"/static/audio/{audio_filename}"
        
        async with SessionLocal() as db:
            # 3. Update message in DB
            from sqlalchemy import update
            from ..models import Message
            await db.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(content=translated_text)
            )
            
            # 4. Create Media record
            db_media = Media(
                message_id=message_id,
                file_path=audio_url,
                file_type="audio/mpeg"
            )
            db.add(db_media)
            await db.commit()
            
            # 5. Notify via WebSocket
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
        print(f"Error in background AI task: {e}")
        # Optionally notify user about failure
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"AI Processing failed: {str(e)}"}),
            user_id
        )

@router.post("/chats/{chat_id}/upload")
async def upload_video_to_chat(
    chat_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: int = 1, # Mock user_id for now
    db: AsyncSession = Depends(get_db)
):
    # Save video temporarily
    file_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp4")
    
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

    # 1. Create initial message in DB
    db_msg = await db_service.create_message(
        db, sender_id=user_id, chat_id=chat_id, content="[Processing video...]", msg_type=MessageType.VIDEO
    )

    # 2. Start background task
    background_tasks.add_task(process_media_ai, db_msg.id, video_path, user_id, chat_id)

    # 3. Broadcast initial "processing" message
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

@router.post("/share")
async def share_result(data: dict):
    # For now, just return success
    return {"status": "success", "message": "Shared successfully"}

# --- New Chat & WebSocket Endpoints ---

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")
            
            # Handle incoming chat message
            if message_type == "chat_message":
                payload = message_data.get("data", {})
                chat_id = payload.get("chat_id")
                content = payload.get("content")
                
                from ..database import SessionLocal
                async with SessionLocal() as db:
                    db_msg = await db_service.create_message(
                        db, sender_id=user_id, chat_id=chat_id, content=content
                    )
                    
                    await manager.broadcast_global({
                        "type": "chat_message",
                        "data": {
                            "id": db_msg.id,
                            "chat_id": db_msg.chat_id,
                            "sender_id": db_msg.sender_id,
                            "content": db_msg.content,
                            "created_at": db_msg.created_at.isoformat()
                        }
                    })

            # Handle WebRTC Signaling (Sprint 3)
            elif message_type == "signal":
                payload = message_data.get("data", {})
                target_id = payload.get("target_id") # Who should receive this signal
                signal_data = payload.get("signal")   # SDP or ICE Candidate
                
                if target_id:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "signal",
                            "data": {
                                "from_id": user_id,
                                "signal": signal_data
                            }
                        }),
                        target_id
                    )
    except Exception as e:
        print(f"WS Error for user {user_id}: {e}")
    finally:
        manager.disconnect(user_id)

@router.get("/chats", response_model=List[schemas.ChatRead])
async def get_chats(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await db_service.get_chats(db, skip=skip, limit=limit)

@router.get("/chats/{chat_id}/messages", response_model=List[schemas.MessageRead])
async def get_messages(chat_id: int, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await db_service.get_messages(db, chat_id=chat_id, skip=skip, limit=limit)
