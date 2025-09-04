import logging
import logging.handlers
import sys
from pathlib import Path
from config.settings import settings

def setup_logger(name: str = None, log_file: str = None) -> logging.Logger:
    """设置日志记录器"""
    if name is None:
        name = __name__
    
    if log_file is None:
        log_file = settings.log_file
    
    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 避免重复添加处理器和传播到父logger
    if logger.handlers:
        return logger
    
    # 启用传播到父logger，让子logger的日志也能显示
    logger.propagate = True
    
    # 创建格式化器
    formatter = logging.Formatter(settings.log_format)
    
    # 文件处理器（按大小轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 创建默认日志记录器
logger = setup_logger("mike_server")
