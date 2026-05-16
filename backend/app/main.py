import logging
import os
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import endpoints, auth
from .database import engine, Base
from .services.file_service import file_service

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Logging sozlamalari
log_handlers = [logging.StreamHandler()]
try:
    log_file = os.path.join(BASE_DIR, "app.log")
    log_handlers.append(logging.FileHandler(log_file))
except (PermissionError, IOError):
    pass  # Production serverda fayl yozishga ruxsat bo'lmasligi mumkin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger("ansor_ai")

app = FastAPI(
    title="Ansor AI - Sign2Voice API",
    description="""
    ## Sign2Voice Professional API
    
    Bu API imo-ishora tilini matnga va ovozga aylantirish uchun xizmat qiladi.
    
    ### Xususiyatlar:
    * **AI Video Processing**: Gemini orqali videoni tahlil qilish.
    * **Text-to-Speech**: Matnni professional ovozga (Edge-TTS) aylantirish.
    * **Real-time Updates**: WebSocket orqali jarayonni kuzatish.
    * **Chat History**: Xabarlar va media tarixini saqlash.
    """,
    version="1.1.0",
    contact={
        "name": "Ansor AI Support",
        "url": "https://ansor.joida.uz/support",
        "email": "support@joida.uz",
    },
    license_info={
        "name": "Proprietary",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# 2. CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. Static fayllar
for folder in ["static/audio", "static/avatars", "uploads", "uploads/files", "uploads/stickers"]:
    full_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")

# 5. Routerlar
app.include_router(auth.router, prefix="/api/v1")
app.include_router(endpoints.router, prefix="/api/v1")

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 6. Global xatoliklar handler'i
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if isinstance(exc, RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
        
    try:
        logger.error(f"Global Error: {str(exc)}", exc_info=True)
    except:
        pass
    
    # Faqat test davomida xatoni to'liq chiqarish (Debug rejimi)
    import traceback
    error_detail = f"DEBUG ERROR: {str(exc)}\nTrace: {traceback.format_exc()}"
    return JSONResponse(
        status_code=500,
        content={"detail": error_detail},
    )

from sqlalchemy import text
from .database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/api/v1/fix-db-schema", tags=["System"])
async def emergency_db_fix(db: AsyncSession = Depends(get_db)):
    """Emergency schema repair tool."""
    try:
        from .database import engine, Base
        # 1. Create all tables from scratch natively
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # 2. Safety execution for existing installations that just need column add
        try:
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);"))
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id);"))
            await db.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;"))
            await db.commit()
        except Exception:
            pass # If it fails because table didn't exist and was just created above, it's perfect.
        
        return {"status": "success", "message": "Database initialized successfully!"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/", tags=["General"])
async def root():
    """Server holatini tekshirish uchun bosh endpoint."""
    return {
        "status": "online",
        "service": "Ansor AI API",
        "version": "1.1.0",
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup():
    logger.info("Server ishga tushmoqda...")
    # Eski fayllarni tozalash (24 soatdan oshgan)
    file_service.cleanup_old_files()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Server to'xtamoqda...")
    await engine.dispose()
