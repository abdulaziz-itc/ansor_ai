from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from .api import endpoints
import os

app = FastAPI(title="Sign2Voice API")

# Enable CORS for Flutter communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static audio files
if not os.path.exists("static/audio"):
    os.makedirs("static/audio")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(endpoints.router)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server Error: {str(exc)}"},
    )

@app.get("/")
async def root():
    return {"message": "Sign2Voice API is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
