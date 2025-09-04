from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import asyncio

from routes import audio, news, admin, game
from services.scheduler import NewsSchedulerService
from config.settings import settings
from utils.logger import logger

# 加载环境变量
load_dotenv()

# 新闻调度器
news_scheduler = NewsSchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    try:
        # Can be controlled via environment variable
        if settings.auto_start_scheduler:
            await news_scheduler.start_scheduler()
            logger.info("News scheduler auto-started")
        else:
            logger.info("News scheduler not auto-started, waiting for manual start")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    yield
    
    # Shutdown
    try:
        await news_scheduler.stop_scheduler()
        logger.info("News scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")

app = FastAPI(
    title=settings.app_name,
    description="Audio to Text Conversion and News Search API using Local Whisper Models and Vector Database",
    version=settings.app_version,
    lifespan=lifespan
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
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(game.router, prefix="/api/game", tags=["game"])


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": f"{settings.app_name} - Audio to Text Conversion and News Search API",
        "version": settings.app_version,
        "endpoints": {
            "health": "/health",
            "audio_transcribe": "/api/audio/transcribe",
            "audio_models": "/api/audio/models",
            "news_search": "/api/news/search",
            "news_health": "/api/news/health",
            "game_replay": "/api/game/replay/{game_id}",
            "game_plays": "/api/game/plays/{game_id}",
            "game_cache": "/api/game/cache/*",
            "admin_scheduler": "/api/admin/scheduler/*",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        scheduler_status = "running" if news_scheduler.is_running else "stopped"
        return {
            "status": "OK", 
            "message": f"{settings.app_name} is running",
            "version": settings.app_version,
            "scheduler_status": scheduler_status
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = settings.port
    host = settings.host
    
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    logger.info(f"监听地址: {host}:{port}")
    
    uvicorn.run(app, host=host, port=port)
