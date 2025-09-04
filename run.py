#!/usr/bin/env python3
"""
Mike Server 启动脚本
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

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
        "main:app",  # 现在可以直接使用main:app
        host=host,
        port=port,
        reload=True,  # 开发模式自动重载
        log_level="warning",  # 降低uvicorn日志级别，避免与自定义logger重复
        access_log=False  # 禁用访问日志，减少重复输出
    )
