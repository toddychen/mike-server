"""
Custom Article class that integrates enhanced date extraction
"""

import logging
from typing import Optional
from datetime import datetime
from newspaper import Article as BaseArticle
from .custom_extractors import CustomDateExtractor


class CustomArticle(BaseArticle):
    """Enhanced Article class with custom date extraction"""
    
    def __init__(self, url: str, **kwargs):
        # Initialize logger first, before any other operations
        self.logger = logging.getLogger(__name__)
        
        # Call parent class __init__ with only the required parameters
        super().__init__(url, **kwargs)
        
        # Initialize custom date extractor
        self.date_extractor = CustomDateExtractor()
        
        # Store the extracted publish date
        self._custom_publish_date = None
    
    def parse(self) -> None:
        """Override parse method to use custom date extraction"""
        # Call the original parse method
        super().parse()
        
        # Extract publish date using our custom extractor
        if self.date_extractor:
            try:
                self._custom_publish_date = self.date_extractor.extract(self)
                if self._custom_publish_date:
                    self.logger.info(f"✅ Custom date extraction successful: {self._custom_publish_date}")
            except Exception as e:
                self.logger.error(f"❌ Custom date extraction failed: {e}")
                self._custom_publish_date = None
    
    
    def get_enhanced_metadata(self) -> dict:
        """Get enhanced metadata including custom date extraction info"""
        metadata = {
            'title': self.title,
            'text': self.text,
            'authors': self.authors,
            'publish_date': self.publish_date if self.publish_date else self._custom_publish_date,
            'url': self.url,
            'canonical_link': self.canonical_link,
            'meta_description': self.meta_description,
            'meta_lang': self.meta_lang,
            'meta_favicon': self.meta_favicon,
            'meta_img': self.meta_img,
            'meta_keywords': self.meta_keywords,
            'tags': self.tags,
            'movies': self.movies,
            'top_image': self.top_image,
            'images': self.images,
            'word_count': len(self.text.split()) if self.text else 0,
        }
        
        # Add custom extraction info
        metadata['custom_publish_date_extraction'] = {
            'used_custom_extractor': self._custom_publish_date is not None,
            'custom_date': self._custom_publish_date,
            'original_date': self.publish_date
        }
        
        return metadata
