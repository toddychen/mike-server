#!/usr/bin/env python3
"""
独立运行新闻调度器的脚本
可以单独运行，不依赖FastAPI应用
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from services.scheduler import NewsSchedulerService
from utils.logger import setup_logger

logger = setup_logger("scheduler_standalone")

class StandaloneScheduler:
    def __init__(self):
        self.scheduler = NewsSchedulerService()
        self.running = False
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.stop()
        sys.exit(0)
    
    async def start(self):
        """启动调度器"""
        try:
            logger.info("启动独立新闻调度器...")
            await self.scheduler.start_scheduler()
            self.running = True
            
            logger.info("调度器已启动，按Ctrl+C停止")
            
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"启动失败: {e}")
            sys.exit(1)
    
    def stop(self):
        """停止调度器"""
        if self.running:
            logger.info("正在停止调度器...")
            asyncio.create_task(self.scheduler.stop_scheduler())
            self.running = False
            logger.info("调度器已停止")

async def main():
    """主函数"""
    scheduler = StandaloneScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已停止")
