import logging
from datetime import datetime
from typing import List, Dict
import signal
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.news_engine import NewsEngine
from config.settings import settings

class NewsSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.news_engine = NewsEngine(mode="FULL")
        self.entity_ids = settings.team_ids  # 保持兼容性，但实际使用entity_id概念
        self.is_running = False
        
        # 设置信号处理器
        self._setup_signal_handlers()
        
        logging.info(f"新闻调度器初始化完成，实体ID: {self.entity_ids}")
        
    def _setup_signal_handlers(self):
        """设置信号处理器，允许通过系统信号控制调度器"""
        def signal_handler(signum, frame):
            if signum == signal.SIGUSR1:  # 启动调度器
                self.start_scheduler()
            elif signum == signal.SIGUSR2:  # 停止调度器
                self.stop_scheduler()
            elif signum == signal.SIGTERM:  # 优雅关闭
                self.stop_scheduler()
                sys.exit(0)
        
        try:
            signal.signal(signal.SIGUSR1, signal_handler)
            signal.signal(signal.SIGUSR2, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            logging.warning(f"设置信号处理器失败: {e}")
    
    async def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            logging.info("调度器已经在运行")
            return
        
        try:
            # 每小时执行一次新闻抓取
            self.scheduler.add_job(
                self.fetch_and_store_news,
                CronTrigger(minute=0),  # 每小时整点执行
                id="news_fetch_job",
                name="新闻抓取任务"
            )
            
            self.scheduler.start()
            self.is_running = True
            logging.info("新闻调度器已启动")
        except Exception as e:
            logging.error(f"启动调度器失败: {e}")
            raise
    
    async def stop_scheduler(self):
        """停止调度器"""
        if not self.is_running:
            logging.info("调度器已经停止")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logging.info("新闻调度器已停止")
        except Exception as e:
            logging.error(f"停止调度器失败: {e}")
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        try:
            status = {
                "is_running": self.is_running,
                "team_ids": self.team_ids,
                "jobs": []
            }
            
            if self.is_running:
                jobs = self.scheduler.get_jobs()
                for job in jobs:
                    status["jobs"].append({
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                        "trigger": str(job.trigger)
                    })
            
            return status
        except Exception as e:
            logging.error(f"获取调度器状态失败: {e}")
            return {"error": str(e)}
    
    def fetch_and_store_news(self):
        """抓取并存储新闻"""
        logging.info("开始执行新闻抓取任务")
        
        total_processed = 0
        total_stored = 0
        
        for entity_id in self.entity_ids:
            try:
                logging.info(f"处理实体 {entity_id} 的新闻")
                
                # 使用NewsEngine获取新闻并存储
                result = self.news_engine.fetch_news_for_entity(entity_id, max_news_count=10)
                
                if result['success']:
                    total_processed += result['metadata_count']
                    total_stored += result['stored_count']
                    logging.info(f"实体 {entity_id} 处理成功: {result['message']}")
                else:
                    logging.warning(f"实体 {entity_id} 处理失败: {result['message']}")
                    
            except Exception as e:
                logging.error(f"处理实体 {entity_id} 的新闻时出错: {e}")
                continue
        
        logging.info(f"新闻抓取任务完成，处理: {total_processed}, 成功存储: {total_stored}")
    
    def manual_trigger(self):
        """手动触发一次新闻抓取任务"""
        if not self.is_running:
            logging.warning("调度器未运行，无法手动触发")
            return False
        
        try:
            # 立即执行一次任务
            self.scheduler.add_job(
                self.fetch_and_store_news,
                trigger='date',
                id="manual_trigger",
                name="手动触发新闻抓取"
            )
            logging.info("手动触发新闻抓取任务")
            return True
        except Exception as e:
            logging.error(f"手动触发失败: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict:
        """获取向量数据库集合统计信息"""
        try:
            info = self.news_engine.storage.get_collection_info()
            return {
                "collection_info": info,
                "scheduler_status": self.get_status()
            }
        except Exception as e:
            logging.error(f"获取集合统计失败: {e}")
            return {"error": str(e)}
