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

# AGAR DATABASE_URL berilmagan bo'lsa, avtomatik ravishda o'zida xotira yaratadigan SQLite ga ulanadi (Hech qanday konfiguratsiya shart emas!)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ansor_ai.db")

# 1. Engine sozlamalari
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite specific settings
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}  # Important for SQLite
    )
else:
    # PostgreSQL specific settings (Production)
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
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
