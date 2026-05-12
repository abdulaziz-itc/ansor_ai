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

# 1. Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
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

# 3. Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} processed in {process_time:.4f}s")
    return response

# 4. Static fayllar
for folder in ["static/audio", "static/avatars", "uploads", "uploads/files", "uploads/stickers"]:
    if not os.path.exists(folder):
        os.makedirs(folder)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 5. Routerlar
app.include_router(auth.router, prefix="/api/v1")
app.include_router(endpoints.router, prefix="/api/v1")

# 6. Global xatoliklar handler'i
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ichki server xatosi yuz berdi. Administrator bilan bog'laning."},
    )

from sqlalchemy import text
from .database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/api/v1/fix-db-schema", tags=["System"])
async def emergency_db_fix(db: AsyncSession = Depends(get_db)):
    """Emergency schema repair tool."""
    try:
        # 1. Add google_id
        await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);"))
        # 2. Add Index
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id);"))
        # 3. Make password nullable
        await db.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;"))
        
        await db.commit()
        return {"status": "success", "message": "Database schema updated successfully via active session!"}
    except Exception as e:
        await db.rollback()
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
