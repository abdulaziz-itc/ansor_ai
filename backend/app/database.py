import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Logger sozlash
logger = logging.getLogger("ansor_ai.database")

# .env yuklash (loyihaning asosiy papkasidan)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# AGAR DATABASE_URL berilmagan bo'lsa, mutlaq (Absolute) manzil bo'yicha SQLite ga ulanadi
DB_PATH = os.path.join(BASE_DIR, "ansor_ai.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

# 1. Engine sozlamalari
# NullPool ishlatiladi: WSGI (Passenger) muhitida har so'rov uchun yangi
# ulanish yaratiladi. Bu a2wsgi event loop muammosini hal qiladi.
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
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
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        try:
            await session.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            await session.close()
        except Exception:
            pass  # Cleanup xatosi response ga ta'sir qilmasligi uchun yutib yuboriladi

logger.info("Ma'lumotlar bazasi dvigateli (Engine) muvaffaqiyatli sozlandi.")
