import os
from typing import Optional, List

class Settings:
    # 应用配置
    app_name: str = "Mike Server"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 3000))
    
    # 文件上传配置
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    upload_dir: str = "data/temp"
    
    # Whisper配置
    whisper_model: str = os.getenv("WHISPER_MODEL", "tiny")
    whisper_cache_dir: str = "data/models"
    
    # GPT API配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # 摘要器模型配置
    summarizer_model: str = os.getenv("SUMMARIZER_MODEL", "gpt-5-nano")
    
    # 其他LLM任务模型配置（预留）
    # llm_task_model: str = os.getenv("LLM_TASK_MODEL", "gpt-4o")
    
    # 向量数据库配置
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", 6333))
    qdrant_collection: str = "news_articles"
    
    # 新闻抓取配置
    news_fetch_interval_hours: int = int(os.getenv("NEWS_FETCH_INTERVAL_HOURS", 1))
    
    # 信息提取配置
    extractable_entity_labels: List[str] = [
        'PERSON',    # 运动员、教练、管理层
        'ORG',       # 球队、联盟、公司
        'LOC',       # 城市、场馆
        'GPE',       # 国家、州
        'FAC',       # 体育场馆
    ]
    
    # 调度器配置
    auto_start_scheduler: bool = os.getenv("AUTO_START_SCHEDULER", "false").lower() == "true"
    scheduler_log_file: str = "logs/scheduler.log"
    
    # 管理员配置
    admin_secret: str = os.getenv("ADMIN_SECRET", "heymike")
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = "logs/app.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 团队配置
    team_ids: List[str] = os.getenv("TEAM_IDS", "team1,team2,team3").split(",")

# 全局设置实例
settings = Settings()
