import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

# Logger sozlash
logger = logging.getLogger("ansor_ai.database")

# .env yuklash (loyihaning asosiy papkasidan)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ansor_ai")

# 1. Engine sozlamalari (Production-ready)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQL so'rovlarini terminalga chiqarmaslik (productionda)
    pool_size=10,         # Doimiy ochiq ulanishlar soni
    max_overflow=20,      # Zarurat tug'ilganda qo'shimcha ulanishlar soni
    pool_timeout=30,      # Ulanish kutish vaqti
    pool_recycle=1800,    # 30 daqiqadan keyin ulanishni yangilash
)

# 2. Session yaratuvchi
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    """Baza bilan seans ochish va yopish uchun generator."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ma'lumotlar bazasi seansi xatosi: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()

logger.info("Ma'lumotlar bazasi dvigateli (Engine) muvaffaqiyatli sozlandi.")
