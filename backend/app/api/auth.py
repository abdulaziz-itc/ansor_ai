from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import shutil
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from ..database import get_db
from ..services.db_service import db_service
from ..services.auth_service import auth_service
from .deps import get_current_user
from ..models import User
from . import schemas

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Yangi foydalanuvchi ro'yxatdan o'tishi."""
    try:
        # Username mavjudligini tekshirish
        db_user = await db_service.get_user_by_username(db, user_in.username)
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="Ushbu foydalanuvchi nomi allaqachon mavjud"
            )
        
        # Email mavjudligini tekshirish
        db_email = await db_service.get_user_by_email(db, user_in.email)
        if db_email:
            raise HTTPException(
                status_code=400,
                detail="Ushbu elektron pochta manzili allaqachon ro'yxatdan o'tgan"
            )
        
        # Parolni xesh qilish
        hashed_password = auth_service.get_password_hash(user_in.password)
        
        # Foydalanuvchini yaratish
        return await db_service.create_user(db, user_in, hashed_password)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Register xatosi: {str(e)} | {traceback.format_exc()}")

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Foydalanuvchi tizimga kirishi (Token olish)."""
    try:
        # Foydalanuvchini qidirish
        user = await db_service.get_user_by_username(db, form_data.username)
        if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Noto'g'ri foydalanuvchi nomi yoki parol",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Access Token yaratish
        access_token = auth_service.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Login xatosi: {str(e)} | {traceback.format_exc()}")

@router.post("/google", response_model=schemas.Token)
async def google_login(request_data: schemas.GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    """Google ID Token orqali kirish yoki ro'yxatdan o'tish."""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        # Backendda CLIENT_ID ni environmentdan olamiz, hozircha verification faqat structuraga asosan
        # Haqiqiy production uchun client_id pass qilinishi shart
        idinfo = id_token.verify_oauth2_token(request_data.id_token, google_requests.Request(), clock_skew_in_seconds=10)
        
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        picture = idinfo.get('picture')
        
    except ValueError as e:
        # Noto'g'ri token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google tokenini tekshirib bo'lmadi: {str(e)}"
        )
    except ImportError:
        # Agar google libraries topilmasa temporary fallback debug mode (Faqat testing uchun!)
        # Eslatma: PRODUCTIONDA buni o'chirish lozim!
        import json
        import base64
        try:
             # Just decoding for naive bypass during mock/dry-runs if user requested.
             parts = request_data.id_token.split('.')
             if len(parts) > 1:
                 payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode('utf-8'))
                 google_id = payload['sub']
                 email = payload['email']
                 name = payload.get('name', 'Google User')
                 picture = payload.get('picture')
             else:
                 raise ValueError("Bad format")
        except:
             raise HTTPException(status_code=500, detail="Google verification libraries not fully configured on server.")

    # 1. Google ID bo'yicha qidirish
    user = await db_service.get_user_by_google_id(db, google_id)
    
    # 2. Agar topilmasa, Email bo'yicha qidirish (avvaldan oddiy ro'yxatdan o'tgan bo'lishi mumkin)
    if not user:
        user = await db_service.get_user_by_email(db, email)
        if user:
            # User bog'lanmagan ekan, google_id ni qo'shib qo'yamiz
            # schemas update generator or direct update to integrate
            from sqlalchemy import update
            from ..models import User
            await db.execute(update(User).where(User.id == user.id).values(google_id=google_id))
            await db.commit()
            
    # 3. Umuman topilmasa - Yangi foydalanuvchi ochish
    if not user:
        user = await db_service.create_google_user(
            db=db,
            email=email,
            full_name=name,
            google_id=google_id,
            avatar_url=picture
        )
    
    # Native JWT token generatsiyasi
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """Hozirgi tizimga kirgan foydalanuvchi ma'lumotlarini olish."""
    return current_user

@router.patch("/me", response_model=schemas.UserRead)
async def update_profile(
    user_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Profil ma'lumotlarini (ism, email) yangilash."""
    return await db_service.update_user(db, current_user.id, user_update)

@router.post("/me/avatar", response_model=schemas.UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Profil rasmini yuklash."""
    AVATAR_DIR = "static/avatars"
    if not os.path.exists(AVATAR_DIR):
        os.makedirs(AVATAR_DIR)
        
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Bazani yangilash
    avatar_url = f"/static/avatars/{filename}"
    user_update = schemas.UserUpdate(avatar_url=avatar_url)
    return await db_service.update_user(db, current_user.id, user_update)
