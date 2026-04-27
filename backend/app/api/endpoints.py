from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import shutil
import os
import uuid
from ..services.ai_service import ai_service
from ..services.audio_service import audio_service

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload-video")
async def upload_video(request: Request):
    # Save video temporarily
    file_id = str(uuid.uuid4())
    content_type = request.headers.get("content-type", "")
    
    video_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp4")
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        video = form.get("video")
        if not video:
            raise HTTPException(status_code=400, detail="Video file required")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
    else:
        with open(video_path, "wb") as buffer:
            async for chunk in request.stream():
                buffer.write(chunk)

    try:
        # 1. Translate video to text using AI
        translated_text = await ai_service.translate_video(video_path)
        
        # 2. Generate audio from text
        audio_filename = await audio_service.generate_audio(translated_text)
        
        # 3. Construct response
        audio_url = f"/static/audio/{audio_filename}"
        
        return {
            "text": translated_text,
            "audio_url": audio_url
        }
    except Exception as e:
        print(f"Error processing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup video file if needed (keeping it for now for easy debugging)
        # if os.path.exists(video_path):
        #     os.remove(video_path)
        pass

@router.post("/share")
async def share_result(data: dict):
    # For now, just return success
    return {"status": "success", "message": "Shared successfully"}
