import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

# Logger sozlash
logger = logging.getLogger("ansor_ai.auth")

# .env yuklash
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Xavfsizlik sozlamalari
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secret-key-change-it-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 hafta

# Parollarni xesh qilish uchun context
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

class AuthService:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Kiritilgan parolni baza bilan solishtirish."""
        if not hashed_password:
            return False
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    def get_password_hash(self, password: str) -> str:
        """Parolni xesh qilish (Bcrypt)."""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Yangi JWT Access Token yaratish."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        """Tokenni tekshirish va ma'lumotlarni olish."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWT Decode Error: {str(e)}")
            return None

auth_service = AuthService()
