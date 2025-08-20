from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from .routes import audio

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="Mike Server",
    description="Audio to Text Conversion API using Local Whisper Models",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "Mike Server - Audio to Text Conversion API using Local Whisper",
        "endpoints": {
            "health": "/health",
            "audio_transcribe": "/api/audio/transcribe",
            "audio_models": "/api/audio/models",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "OK", "message": "Mike Server is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
