import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Set, Dict, List, Optional

class ProcessStatusTracker:
    """Process status tracker to track processing states for news content"""
    
    # Class-level logger
    logger = logging.getLogger(__name__)
    
    def __init__(self, cache_file: str = "data/process_status.json", lookback_days: int = 10):
        self.cache_file = Path(cache_file)
        self.lookback_days = lookback_days
        # New schema: {date: {success: [uuid], fetch_failed: [uuid], summary_failed: [uuid], storage_failed: [uuid]}}
        self.process_status_cache: Dict[str, Dict[str, List[str]]] = {}
        self.ensure_data_directory()
        self.load_cache()
        
        self.logger.info(f"Process status tracker initialized, cache file: {self.cache_file}, lookback days: {self.lookback_days}")
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_utc_date_key(self, timestamp: float = None) -> str:
        """Get UTC date key, format: YYYY-MM-DD"""
        if timestamp is None:
            timestamp = time.time()
        
        # Convert to UTC time
        utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return utc_time.strftime("%Y-%m-%d")
    
    def _ensure_date_entry(self, date_key: str):
        """Ensure date entry exists with all required categories"""
        if date_key not in self.process_status_cache:
            self.process_status_cache[date_key] = {
                'success': [],
                'fetch_failed': [],
                'summary_failed': [],
                'extraction_failed': [],
                'storage_failed': []
            }
    
    def load_cache(self):
        """Load cache from JSON file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.process_status_cache = json.load(f)
                
                # Ensure all dates have the required structure
                for date_key in self.process_status_cache:
                    self._ensure_date_entry(date_key)
                
                total_entries = sum(len(cat) for date_data in self.process_status_cache.values() 
                                  for cat in date_data.values())
                self.logger.info(f"Loaded {total_entries} process status entries from cache file")
            else:
                self.logger.info("Cache file does not exist, creating new cache")
                self.process_status_cache = {}
        except Exception as e:
            self.logger.error(f"Failed to load cache file: {e}")
            self.process_status_cache = {}
    
    def save_cache(self):
        """Save cache to JSON file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.process_status_cache, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Cache saved to: {self.cache_file}")
        except Exception as e:
            self.logger.error(f"Failed to save cache file: {e}")
    
    def is_content_id_processed(self, content_id: str) -> bool:
        """Check if content ID has already been successfully processed"""
        recent_ids = self.get_recent_success_ids()
        return content_id in recent_ids
    
    def mark_fetch_failed(self, content_id: str):
        """Mark content ID as fetch failed"""
        today_key = self.get_utc_date_key()
        self._ensure_date_entry(today_key)
        
        if content_id not in self.process_status_cache[today_key]['fetch_failed']:
            self.process_status_cache[today_key]['fetch_failed'].append(content_id)
            self.save_cache()
            self.logger.info(f"Marked content ID as fetch failed: {content_id}")
    
    def mark_summary_failed(self, content_id: str):
        """Mark content ID as summary failed"""
        today_key = self.get_utc_date_key()
        self._ensure_date_entry(today_key)
        
        if content_id not in self.process_status_cache[today_key]['summary_failed']:
            self.process_status_cache[today_key]['summary_failed'].append(content_id)
            self.save_cache()
            self.logger.info(f"Marked content ID as summary failed: {content_id}")
    
    def mark_storage_failed(self, content_id: str):
        """Mark content ID as storage failed"""
        today_key = self.get_utc_date_key()
        self._ensure_date_entry(today_key)
        
        if content_id not in self.process_status_cache[today_key]['storage_failed']:
            self.process_status_cache[today_key]['storage_failed'].append(content_id)
            self.save_cache()
            self.logger.info(f"Marked content ID as storage failed: {content_id}")
    
    def mark_extraction_failed(self, content_id: str):
        """Mark content ID as extraction failed"""
        today_key = self.get_utc_date_key()
        self._ensure_date_entry(today_key)
        
        if content_id not in self.process_status_cache[today_key]['extraction_failed']:
            self.process_status_cache[today_key]['extraction_failed'].append(content_id)
            self.save_cache()
            self.logger.info(f"Marked content ID as extraction failed: {content_id}")
    
    def mark_success(self, content_id: str):
        """Mark content ID as successfully processed"""
        today_key = self.get_utc_date_key()
        self._ensure_date_entry(today_key)
        
        if content_id not in self.process_status_cache[today_key]['success']:
            self.process_status_cache[today_key]['success'].append(content_id)
            self.save_cache()
            self.logger.info(f"Marked content ID as successfully processed: {content_id}")
    
    def move_to_success(self, content_id: str, from_category: str):
        """Move UUID from a failed category to success category"""
        today_key = self.get_utc_date_key()
        self._ensure_date_entry(today_key)
        
        if from_category not in ['fetch_failed', 'summary_failed', 'extraction_failed', 'storage_failed']:
            self.logger.error(f"Invalid category: {from_category}")
            return False
        
        # Remove from failed category
        if content_id in self.process_status_cache[today_key][from_category]:
            self.process_status_cache[today_key][from_category].remove(content_id)
            self.logger.info(f"Removed {content_id} from {from_category}")
        
        # Add to success category
        if content_id not in self.process_status_cache[today_key]['success']:
            self.process_status_cache[today_key]['success'].append(content_id)
            self.logger.info(f"Moved {content_id} to success category")
        
        self.save_cache()
        return True
    
    def get_recent_success_ids(self) -> Set[str]:
        """Get successfully processed content ID set from last N days"""            
        current_timestamp = time.time()
        day_seconds = 24 * 3600
        
        recent_success_ids = set()
        for i in range(self.lookback_days):
            target_timestamp = current_timestamp - (i * day_seconds)
            date_key = self.get_utc_date_key(target_timestamp)
            if date_key in self.process_status_cache:
                recent_success_ids.update(self.process_status_cache[date_key]['success'])
        
        return recent_success_ids
    
    def get_recent_failed_ids(self) -> Dict[str, List[str]]:
        """Get failed content IDs by category from last N days"""
        current_timestamp = time.time()
        day_seconds = 24 * 3600
        
        recent_failed_ids = {
            'fetch_failed': [],
            'summary_failed': [],
            'extraction_failed': [],
            'storage_failed': []
        }
        
        for i in range(self.lookback_days):
            target_timestamp = current_timestamp - (i * day_seconds)
            date_key = self.get_utc_date_key(target_timestamp)
            if date_key in self.process_status_cache:
                recent_failed_ids['fetch_failed'].extend(self.process_status_cache[date_key]['fetch_failed'])
                recent_failed_ids['summary_failed'].extend(self.process_status_cache[date_key]['summary_failed'])
                recent_failed_ids['extraction_failed'].extend(self.process_status_cache[date_key]['extraction_failed'])
                recent_failed_ids['storage_failed'].extend(self.process_status_cache[date_key]['storage_failed'])
        
        return recent_failed_ids
    
    def get_failed_ids_by_category(self, date_key: Optional[str] = None) -> Dict[str, List[str]]:
        """Get failed IDs by category for a specific date (default: today)"""
        if date_key is None:
            date_key = self.get_utc_date_key()
        
        self._ensure_date_entry(date_key)
        return {
            'fetch_failed': self.process_status_cache[date_key]['fetch_failed'].copy(),
            'summary_failed': self.process_status_cache[date_key]['summary_failed'].copy(),
            'extraction_failed': self.process_status_cache[date_key]['extraction_failed'].copy(),
            'storage_failed': self.process_status_cache[date_key]['storage_failed'].copy()
        }
    
    def get_success_ids(self, date_key: Optional[str] = None) -> List[str]:
        """Get successful IDs for a specific date (default: today)"""
        if date_key is None:
            date_key = self.get_utc_date_key()
        
        self._ensure_date_entry(date_key)
        return self.process_status_cache[date_key]['success'].copy()
    
    def cleanup_old_dates(self, days: int = 30):
        """Clean up data older than specified days"""
        current_timestamp = time.time()
        day_seconds = 24 * 3600
        
        dates_to_remove = []
        for date_key in self.process_status_cache.keys():
            try:
                # Parse date
                date_obj = datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                date_timestamp = date_obj.timestamp()
                
                if current_timestamp - date_timestamp > days * day_seconds:
                    dates_to_remove.append(date_key)
            except ValueError:
                dates_to_remove.append(date_key)
        
        for date_key in dates_to_remove:
            removed_count = sum(len(self.process_status_cache[date_key][cat]) 
                              for cat in self.process_status_cache[date_key])
            del self.process_status_cache[date_key]
            self.logger.info(f"Cleaned up expired date {date_key}, removed {removed_count} entries")
        
        if dates_to_remove:
            self.save_cache()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_success = sum(len(data['success']) for data in self.process_status_cache.values())
        total_fetch_failed = sum(len(data['fetch_failed']) for data in self.process_status_cache.values())
        total_summary_failed = sum(len(data['summary_failed']) for data in self.process_status_cache.values())
        total_extraction_failed = sum(len(data['extraction_failed']) for data in self.process_status_cache.values())
        total_storage_failed = sum(len(data['storage_failed']) for data in self.process_status_cache.values())
        date_count = len(self.process_status_cache)
        
        return {
            "total_success": total_success,
            "total_fetch_failed": total_fetch_failed,
            "total_summary_failed": total_summary_failed,
            "total_extraction_failed": total_extraction_failed,
            "total_storage_failed": total_storage_failed,
            "date_count": date_count,
            "cache_file": str(self.cache_file),
            f"recent_{self.lookback_days}_days_success": len(self.get_recent_success_ids())
        }
    
    def get_daily_summary(self, date_key: Optional[str] = None) -> Dict:
        """Get daily summary for a specific date (default: today)"""
        if date_key is None:
            date_key = self.get_utc_date_key()
        
        self._ensure_date_entry(date_key)
        date_data = self.process_status_cache[date_key]
        
        return {
            "date": date_key,
            "success_count": len(date_data['success']),
            "fetch_failed_count": len(date_data['fetch_failed']),
            "summary_failed_count": len(date_data['summary_failed']),
            "extraction_failed_count": len(date_data['extraction_failed']),
            "storage_failed_count": len(date_data['storage_failed']),
            "total_processed": sum(len(cat) for cat in date_data.values())
        }
    
    def remove_from_failed_category(self, content_id: str, category: str, date_key: Optional[str] = None):
        """Remove content_id from a specific failed category for a specific date (default: today)"""
        if date_key is None:
            date_key = self.get_utc_date_key()
        
        if category not in ['fetch_failed', 'summary_failed', 'extraction_failed', 'storage_failed']:
            self.logger.error(f"Invalid category: {category}")
            return False
        
        self._ensure_date_entry(date_key)
        
        if content_id in self.process_status_cache[date_key][category]:
            self.process_status_cache[date_key][category].remove(content_id)
            self.save_cache()
            self.logger.info(f"Removed {content_id} from {category} for date {date_key}")
            return True
        
        return False
    
    def cleanup_past_failed_entries(self, content_id: str, failed_ids_by_category: Dict[str, List[str]]):
        """Clean up any existing failed entries for this content_id from past days using pre-fetched data"""
        try:
            # Check if content_id exists in any failed category using pre-fetched data
            for category in ['fetch_failed', 'summary_failed', 'extraction_failed', 'storage_failed']:
                if content_id in failed_ids_by_category[category]:
                    self.logger.info(f"Found existing {category} entry for {content_id}, cleaning up...")
                    
                    # Get all dates and clean up this content_id from failed categories
                    current_timestamp = time.time()
                    day_seconds = 24 * 3600
                    
                    for i in range(self.lookback_days):  # Check last N days
                        target_timestamp = current_timestamp - (i * day_seconds)
                        date_key = self.get_utc_date_key(target_timestamp)
                        
                        # Remove content_id from this failed category for this date
                        if self.remove_from_failed_category(content_id, category, date_key):
                            self.logger.info(f"Successfully removed {content_id} from {category} for date {date_key}")
                    
                    break  # Found in one category, no need to check others
                    
        except Exception as e:
            self.logger.error(f"Error during cleanup of past failed entries: {e}")
            # Don't fail the main process for cleanup errors
    

