#!/usr/bin/env python3
"""
初始化数据库和集合的脚本
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from config.database import init_qdrant_collections
from utils.logger import setup_logger

logger = setup_logger("db_init")

def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        
        # 初始化Qdrant集合
        init_qdrant_collections()
        
        logger.info("数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
