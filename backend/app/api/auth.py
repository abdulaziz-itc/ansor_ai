from fastapi import APIRouter, Depends, HTTPException, status
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
    # Username mavjudligini tekshirish
    db_user = await db_service.get_user_by_username(db, user_in.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Ushbu foydalanuvchi nomi allaqachon mavjud"
        )
    
    # Parolni xesh qilish
    hashed_password = auth_service.get_password_hash(user_in.password)
    
    # Foydalanuvchini yaratish
    return await db_service.create_user(db, user_in, hashed_password)

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Foydalanuvchi tizimga kirishi (Token olish)."""
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

@router.get("/me", response_model=schemas.UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """Hozirgi tizimga kirgan foydalanuvchi ma'lumotlarini olish."""
    return current_user
