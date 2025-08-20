#!/usr/bin/env python3
"""
Mike Server 启动脚本
"""

import uvicorn
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 3000))
    
    print("🚀 启动 Mike Server...")
    print(f"📡 服务器地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔍 健康检查: http://{host}:{port}/health")
    
    # 启动服务器
    uvicorn.run(
        "src.main:app",  # 使用模块路径
        host=host,
        port=port,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )
