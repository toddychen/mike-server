"""
Custom extractors for newspaper3k to enhance date extraction
"""

import logging
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

class CustomDateExtractor:
    """Independent date extractor that supports HTML5 time tags and other modern date formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, article) -> Optional[datetime]:
        """
        Enhanced date extraction with HTML5 time tag support
        
        Args:
            article: newspaper3k Article object
            
        Returns:
            Parsed datetime or None if extraction fails
        """
        try:
            # Use article.html field directly with BeautifulSoup
            if not hasattr(article, 'html') or not article.html:
                self.logger.warning("⚠️ Article has no HTML content")
                return None
            
            soup = BeautifulSoup(article.html, "html.parser")
            
            # Strategy 1: Look for time tags within content-timestamp div (most specific for Yahoo Sports)
            # Use CSS selector as in the example
            time_tag = soup.select_one("div.content-timestamp time")
            if time_tag and time_tag.has_attr('datetime'):
                datetime_attr = time_tag.get('datetime')
                # self.logger.info(f"✅ Found Yahoo Sports time tag: {datetime_attr}")
                
                parsed_date = self._parse_datetime_attribute(datetime_attr)
                if parsed_date:
                    return parsed_date
            else:
                self.logger.warning("⚠️ No time tag with datetime found in content-timestamp div")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting publish date from HTML5 time tags: {e}")
            import traceback
            self.logger.error(f"Error stack trace: {traceback.format_exc()}")
            return None
    
    def _parse_datetime_attribute(self, datetime_attr: str) -> Optional[datetime]:
        """Parse datetime attribute from HTML5 time tag"""
        try:
            # Remove milliseconds and timezone for simpler parsing
            # Handle format like "2025-08-23T13:30:04.000Z"
            datetime_str = datetime_attr.replace('Z', '')  # Remove Z timezone
            
            # Remove milliseconds part (.000, .123, etc.)
            if '.' in datetime_str:
                datetime_str = datetime_str.split('.')[0]
            
            # Try different datetime formats
            for fmt in [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]:
                try:
                    parsed_date = datetime.strptime(datetime_str, fmt)
                    return parsed_date
                except ValueError:
                    continue
                    
        except Exception as e:
            self.logger.info(f"Failed to parse datetime attribute: {e}")
        
        return None
