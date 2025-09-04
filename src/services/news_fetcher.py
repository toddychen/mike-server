import logging
import re
from datetime import datetime
from typing import Dict, Optional

from newspaper import Config

from .custom_article import CustomArticle

class NewsFetcher:
    """Service specifically responsible for scraping news content from URLs"""
    
    def __init__(self):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Configure newspaper3k
        self.config = Config()
        self.config.browser_user_agent = 'Mozilla/5.0 (compatible; NewsEngine/1.0)'
        self.config.request_timeout = 30
        self.config.fetch_images = False
        self.config.memoize_articles = False  # No caching, ensure latest content
        
    def fetch(self, url: str) -> Optional[Dict]:
        """Fetch news content from URL using enhanced date extraction"""
        try:
            self.logger.info(f"Starting to scrape news: {url}")
            
            # Create CustomArticle object with enhanced date extraction
            article = CustomArticle(url, config=self.config)
            
            # Download and parse
            article.download()
            if not article.download_state == 2:  # 2 indicates successful download
                raise Exception(f"Download failed, status code: {article.download_state}")
            
            article.parse()
            
            # Skip NLP processing to avoid NLTK data dependency issues
            # article.nlp()  # Comment out NLP processing
            
            # Get enhanced metadata including custom date extraction info
            enhanced_metadata = article.get_enhanced_metadata()
            
            # Preprocess text
            text = enhanced_metadata.get('text', '').strip()
            preprocessed_text = self._preprocess_text(text)
            logging.info(f"Text preprocessed: {len(preprocessed_text)} characters")

            # Extract information
            result = {
                'title': enhanced_metadata.get('title', 'No title'),
                'text': preprocessed_text,
                'authors': enhanced_metadata.get('authors', []),
                'publish_date': enhanced_metadata.get('publish_date'),
                'keywords': enhanced_metadata.get('meta_keywords', []),
                'summary': enhanced_metadata.get('summary', ''),
                'meta_description': enhanced_metadata.get('meta_description', ''),
                'meta_lang': enhanced_metadata.get('meta_lang', 'zh'),
                'canonical_link': enhanced_metadata.get('canonical_link', url),
                'url': url,
                'word_count': enhanced_metadata.get('word_count', 0),
                'extraction_time': datetime.now(),
                'custom_extraction_info': enhanced_metadata.get('custom_publish_date_extraction', {})
            }
            
            self.logger.info(f"Successfully scraped news: {result['title']}, word count: {result['word_count']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to scrape news {url}: {e}")
            return None
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for model input"""
        if not text:
            return ""

        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove advertisement-related content
        patterns_to_remove = [
            r'Advertisement',
            r'--\s*\w+',  # bylines
            r'Copyright.*',
            r'All rights reserved.*'
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()