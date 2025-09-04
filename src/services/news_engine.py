import requests
import logging
import time
import traceback
import uuid
from typing import List, Dict, Optional

from models.news import NewsContent, NewsMetadata
from config.settings import settings
from services.news_fetcher import NewsFetcher
from services.news_storage import NewsStorage
from services.process_status_tracker import ProcessStatusTracker
from services.news_summarizer import NewsSummarizer
from services.information_extractor import InformationExtractor

class NewsEngine:
    """Service responsible for fetching news metadata from Yahoo Sports API, calling scraper, and storing to vector database"""
    
    def __init__(self, mode: str = "FULL"):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        """
        Initialize NewsEngine
        
        Args:
            mode: Processing mode. Options:
                - "FULL": Complete processing (fetch → summary → extract → store)
                - "TIL_FETCH": Stop after fetch step
                - "TIL_SUMMARY": Stop after summary step  
                - "TIL_EXTRACT": Stop after extract step
                - "TIL_STORE": Stop after store step
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Initialize dependent services
        self.fetcher = NewsFetcher()
        self.summarizer = NewsSummarizer()
        self.storage = NewsStorage()
        self.process_tracker = ProcessStatusTracker(lookback_days=10)
        self.information_extractor = InformationExtractor()
        
        # Configuration
        self.yahoo_sports_api_base = "https://mrest.sports.yahoo.com/api/v8/team"
        self.sleep_seconds = 2  # Delay between processing news items
        
        # Mode configuration
        self.mode = mode
        
        self.logger.info(f"NewsEngine initialized with mode: {mode}")
    
    def _should_stop_after_fetch(self) -> bool:
        """Check if should stop after fetch step"""
        if self.mode == "TIL_FETCH":
            self.logger.info(f"🛑 Stopping after fetch step due to mode: {self.mode}")
            return True
        return False
    
    def _should_stop_after_summary(self) -> bool:
        """Check if should stop after summary step"""
        if self.mode == "TIL_SUMMARY":
            self.logger.info(f"🛑 Stopping after summary step due to mode: {self.mode}")
            return True
        return False
    
    def _should_stop_after_extract(self) -> bool:
        """Check if should stop after extract step"""
        if self.mode == "TIL_EXTRACT":
            self.logger.info(f"🛑 Stopping after extract step due to mode: {self.mode}")
            return True
        return False
    
    def _should_stop_after_store(self) -> bool:
        """Check if should stop after store step"""
        if self.mode == "TIL_STORE":
            self.logger.info(f"🛑 Stopping after store step due to mode: {self.mode}")
            return True
        return False

    def fetch_news_for_entity(self, entity_id: str, max_news_count: int = 10) -> Dict:
        """Fetch news for specified entity and store to vector database"""
        try:
            self.logger.info(f"{'-'*60}")
            self.logger.info(f"Starting to fetch news for entity {entity_id}")
            self.logger.info(f"{'-'*60}")
            
            # 1. Get news metadata
            news_metadata = self._fetch_yahoo_sports_news(entity_id)
            if not news_metadata:
                self.logger.warning(f"No news found for entity {entity_id}")
                return {'success': False, 'message': 'No news found', 'stored_count': 0}
            
            # Limit news count
            news_metadata = news_metadata[:max_news_count]
            self.logger.info(f"Retrieved {len(news_metadata)} news metadata")
            
            # 2. Process each news item individually: fetch → summary → storage
            processed_results = self._process_news_items(news_metadata)
            
            result = {
                'success': True,
                'message': f'Successfully processed {len(news_metadata)} news',
                'metadata_count': len(news_metadata),
                'fetched_count': processed_results['fetched_count'],
                'summarized_count': processed_results['summarized_count'],
                'extracted_count': processed_results['extracted_count'],
                'stored_count': processed_results['stored_count']
            }
            
            self.logger.info(f"Entity {entity_id} news processing completed: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to fetch news for entity {entity_id}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}', 'stored_count': 0}
    
    def _process_news_items(self, news_metadata: List[NewsMetadata]) -> Dict:
        """Process each news item individually: fetch → summary → storage"""
        self.logger.info(f"Starting to process {len(news_metadata)} news items individually")
        
        # Get recent success IDs and failed IDs once before the loop
        recent_success_ids = self.process_tracker.get_recent_success_ids()
        recent_failed_ids = self.process_tracker.get_recent_failed_ids()
        
        total_failed = sum(len(ids) for ids in recent_failed_ids.values())
        self.logger.info(f"Found {len(recent_success_ids)} already processed content IDs in last {self.process_tracker.lookback_days} days")
        self.logger.info(f"Found {total_failed} failed content IDs in last {self.process_tracker.lookback_days} days")
        
        fetched_count = 0
        summarized_count = 0
        extracted_count = 0
        stored_count = 0
        
        for i, metadata in enumerate(news_metadata):
            try:
                self.logger.info(f"{'='*40}")
                self.logger.info(f"Processing news item {i+1}/{len(news_metadata)}: {metadata.title}")
                self.logger.info(f"{'='*40}")
                
                # Step 0: Check if already successfully processed in last N days
                if metadata.content_id in recent_success_ids:
                    self.logger.info(f"ContentId already successfully processed in last {self.process_tracker.lookback_days} days, skipping: {metadata.content_id}")
                    continue
                
                # Clean up any existing failed entries from past days using pre-fetched data
                self.process_tracker.cleanup_past_failed_entries(metadata.content_id, recent_failed_ids)
                
                # Step 1: Fetch content
                self.logger.info(f"Step 1: Fetching content from {metadata.url}")
                content = self._fetch_single_news(metadata)
                if not content:
                    self.logger.warning(f"Failed to fetch content for: {metadata.title}")
                    self.process_tracker.mark_fetch_failed(metadata.content_id)
                    continue
                fetched_count += 1
                
                # Check if should stop after fetch step
                if self._should_stop_after_fetch():
                    continue
                
                # Step 2: Generate summary
                self.logger.info(f"Step 2: Generating summary")
                summary_result = self._summarize_single_news(content['text'])
                if not summary_result['success']:
                    self.logger.warning(f"Failed to generate summary for: {metadata.title}")
                    self.process_tracker.mark_summary_failed(metadata.content_id)
                    continue
                summarized_count += 1
                
                # Check if should stop after summary step
                if self._should_stop_after_summary():
                    continue
                
                # Step 3: Extract information from summary
                self.logger.info(f"Step 3: Extracting information from summary")
                info_result = self._extract_info_single_news(summary_result['summary'])
                if not info_result['success']:
                    self.logger.warning(f"Failed to extract information for: {metadata.title}")
                    self.process_tracker.mark_extraction_failed(metadata.content_id)
                    continue
                else:
                    extracted_entities = info_result['entities']
                    extracted_count += 1
                
                # Check if should stop after extract step
                if self._should_stop_after_extract():
                    continue
                
                # Step 4: Store to database
                self.logger.info(f"Step 4: Storing to vector database")
                storage_success = self._store_single_news(metadata, content, summary_result['summary'], extracted_entities)
                if not storage_success:
                    self.logger.error(f"Failed to store: {metadata.title}")
                    self.process_tracker.mark_storage_failed(metadata.content_id)
                    continue
                stored_count += 1
                
                # Check if should stop after store step
                if self._should_stop_after_store():
                    continue
                
                # All steps successful - mark as success and ensure no failed entries exist
                self.process_tracker.mark_success(metadata.content_id)
                self.logger.info(f"✅ All steps completed successfully for: {metadata.title}")
                
                # Add delay between items
                if i < len(news_metadata) - 1:  # Don't delay after the last item
                    self.logger.info(f"Waiting {self.sleep_seconds} second before next item...")
                    time.sleep(self.sleep_seconds)
                
            except Exception as e:
                self.logger.error(f"Exception during processing news item {i+1}: {e}")
                self.logger.error(f"Error stack trace: {traceback.format_exc()}")
                # Mark as fetch failed for unexpected exceptions
                self.process_tracker.mark_fetch_failed(metadata.content_id)
                continue
        
        self.logger.info(f"Batch processing completed: {len(news_metadata)} started, {stored_count} finished (stored)")
        return {
            'fetched_count': fetched_count,
            'summarized_count': summarized_count,
            'extracted_count': extracted_count,
            'stored_count': stored_count
        }
    

    
    def _fetch_single_news(self, metadata: NewsMetadata) -> Optional[Dict]:
        """Fetch content for a single news item"""
        try:
            content = self.fetcher.fetch(metadata.url)
            if content:
                # Use scraped publish date to fill metadata
                if content.get('publish_date') and metadata.published_at is None:
                    metadata.published_at = content['publish_date']
                    self.logger.debug(f"Using scraped publish date: {metadata.published_at}")
                
                self.logger.info(f"✅ Content fetched successfully: {len(content['text'])} characters, {len(content['text'].split())} words")
                return content
            else:
                self.logger.error(f"❌ Failed to fetch content from: {metadata.url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Exception during content fetching: {e}")
            return None
    
    def _summarize_single_news(self, text: str) -> Dict:
        """Generate summary for a single news item"""
        try:
            # Generate summary
            summary_result = self.summarizer.summarize(text)
            
            if summary_result['success']:
                summary = summary_result['summary']
                word_count = summary_result.get('summary_word_count', 0)
                self.logger.info(f"✅ Summary generated successfully: {word_count} words")
                return summary_result
            else:
                self.logger.error(f"❌ Summarization failed: {summary_result.get('error', 'Unknown error')}")
                return summary_result
                
        except Exception as e:
            self.logger.error(f"Exception during summarization: {e}")
            return {
                'success': False,
                'error': str(e),
                'summary': ''
            }
    
    def _extract_info_single_news(self, summary_text: str) -> Dict:
        """Extract information from summary text with simplified structure"""
        try:
            # Use InformationExtractor to extract all entities
            extraction_result = self.information_extractor.extract_entities(summary_text)
            
            # Filter only configured labels and simplify data structure
            filtered_entities = {}
            
            for label in settings.extractable_entity_labels:
                if label in extraction_result.entities:
                    # Only keep text and confidence, and remove duplicates
                    simplified_entities = []
                    seen_texts = set()  # Track seen text to avoid duplicates
                    
                    for entity in extraction_result.entities[label]:
                        entity_text = entity.text.strip()
                        if entity_text and entity_text not in seen_texts:
                            simplified_entities.append({
                                "text": entity_text,
                                "confidence": round(entity.confidence, 3)
                            })
                            seen_texts.add(entity_text)
                    
                    filtered_entities[label] = simplified_entities
            
            entity_count = sum(len(entities) for entities in filtered_entities.values())
            self.logger.info(f"✅ Information extraction completed: {entity_count} entities across {len(filtered_entities)} categories")
            # Log extracted entities in a more readable format
            if filtered_entities:
                self.logger.info("📋 Extracted entities:")
                for label, entities in filtered_entities.items():
                    if entities:
                        entity_list = [f"({entity['text']} | {entity['confidence']})" for entity in entities]
                        self.logger.info(f"  {label}: {', '.join(entity_list)}")
                    else:
                        self.logger.info(f"  {label}: (none)")
            else:
                self.logger.info("📋 Extracted entities: (none)")
            
            return {
                'success': True,
                'entities': filtered_entities
            }
            
        except Exception as e:
            self.logger.error(f"Exception during information extraction: {e}")
            return {
                'success': False,
                'error': str(e),
                'entities': {}
            }
    
    def _store_single_news(self, metadata: NewsMetadata, content: Dict, summary: str, extracted_entities: Dict = None) -> bool:
        """Store a single news item to vector database"""
        try:
            # Create NewsContent object with summary and extracted entities
            news_content = NewsContent(
                content_id=metadata.content_id,
                metadata=metadata,
                content=content['text'],
                summary=summary,
                extracted_entities=extracted_entities,
                embedding=None  # Vector database service will generate embedding based on summary
            )
            
            # Store to vector database
            success = self.storage.store_news(news_content)
            return success
            
        except Exception as e:
            self.logger.error(f"Exception during news storage: {e}")
            return False
    
    def _fetch_yahoo_sports_news(self, entity_id: str) -> List[NewsMetadata]:
        """Fetch news from Yahoo Sports API"""
        try:
            # Build API URL
            api_url = f"{self.yahoo_sports_api_base}/{entity_id}/page?tabs=NEWS"
            # logging.info(f"Requesting Yahoo Sports API: {api_url}")
            
            # Send request
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Parse news data
            news_list = []
            total_news_found = 0
            
            # Check response structure
            if 'Tabs' in data and 'NEWS' in data['Tabs']:
                news_tab = data['Tabs']['NEWS']
                
                if 'Cards' in news_tab:
                    cards = news_tab['Cards']
                    
                    for card in cards:
                        if isinstance(card, dict) and 'Modules' in card:
                            modules = card['Modules']
                            
                            for module in modules:
                                if isinstance(module, dict):
                                    module_type = module.get('Type', 'UNKNOWN')
                                    
                                    # Process main news
                                    if module_type == 'NEWS' and 'News' in module:
                                        news_data = module['News']
                                        total_news_found += 1
                                        
                                        if self._is_valid_yahoo_news(news_data):
                                            news_metadata = self._create_news_metadata_from_yahoo(news_data, entity_id)
                                            if news_metadata:
                                                news_list.append(news_metadata)
                                    
                                    # Process news list
                                    elif module_type == 'NEWS_LIST' and 'NewsList' in module:
                                        news_list_data = module['NewsList']
                                        
                                        for news_item in news_list_data:
                                            total_news_found += 1
                                            
                                            if self._is_valid_yahoo_news(news_item):
                                                news_metadata = self._create_news_metadata_from_yahoo(news_item, entity_id)
                                                if news_metadata:
                                                    news_list.append(news_metadata)
            
            self.logger.info(f"Yahoo Sports API returned {total_news_found} news, filtering to {len(news_list)} valid news")
            return news_list
            
        except Exception as e:
            self.logger.error(f"Failed to fetch news from Yahoo Sports API: {e}")
            self.logger.error(f"Detailed error information: {traceback.format_exc()}")
            return []
    
    def _is_valid_yahoo_news(self, news_data: Dict) -> bool:
        """Validate Yahoo news data validity"""
        # Check if required fields exist and are not empty
        required_fields = ['Title', 'ContentUrl', 'ContentType']
        if not all(field in news_data for field in required_fields):
            return False
        
        # Check Title is not empty
        if not news_data['Title'] or not news_data['Title'].strip():
            return False
        
        # Check URL is not empty
        if not news_data['ContentUrl'] or not news_data['ContentUrl'].strip():
            return False
        
        # Check ContentType must be STORY
        if news_data['ContentType'] != 'STORY':
            return False
        
        return True
    
    def _create_news_metadata_from_yahoo(self, news_data: Dict, entity_id: str) -> Optional[NewsMetadata]:
        """Create NewsMetadata object from Yahoo news data"""
        try:
            # Extract required fields
            title = news_data.get('Title', 'No title')
            content_url = news_data.get('ContentUrl', '')
            content_id = news_data.get('ContentId', '')
            author = news_data.get('Author', 'Unknown author')
            content_type = news_data.get('ContentType', 'STORY')
            
            # Generate ContentId if not available
            if not content_id:
                content_id = str(uuid.uuid4())
            
            # Create NewsMetadata object
            news_metadata = NewsMetadata(
                content_id=content_id,
                url=content_url,
                title=title,
                published_at=None,  # Leave empty, let scraper fill actual publish time
                entity_id=entity_id,
                source=author,  # Use Author field from Yahoo Sports API
                content_type=content_type
            )
            
            return news_metadata
            
        except Exception as e:
            self.logger.error(f"Failed to create news metadata: {e}")
            return None
    
    def get_news_urls(self, entity_id: str) -> List[Dict]:
        """Get news URL list for specified entity (without scraping content)"""
        try:
            self.logger.info(f"Getting news URL list for entity {entity_id}")
            
            # Get news metadata from Yahoo Sports API
            news_metadata = self._fetch_yahoo_sports_news(entity_id)
            
            # Extract URLs
            urls = []
            for metadata in news_metadata:
                urls.append({
                    'title': metadata.title,
                    'url': metadata.url,
                    'source': metadata.source,
                    'published_at': metadata.published_at
                })
            
            self.logger.info(f"Retrieved {len(urls)} news URLs")
            return urls
            
        except Exception as e:
            self.logger.error(f"Failed to get news URL list: {e}")
            return []
    
    def update_existing_points_with_extraction(self, batch_size: int = 10, dry_run: bool = False, get_all: bool = False) -> Dict:
        """
        Update existing points in Qdrant that don't have extracted_entities field
        
        Args:
            batch_size: Number of points to process in each batch
            dry_run: If True, only simulate the process without writing to database
            get_all: If True, process all points without extracted_entities field
            
        Returns:
            Dict with processing statistics
        """
        try:
            if dry_run:
                self.logger.info(f"Starting DRY RUN to update existing points with information extraction")
            else:
                self.logger.info(f"Starting to update existing points with information extraction")
            
            # Get points without extracted_entities field
            points_without_extraction = self.storage.get_points_without_extraction(batch_size, get_all)
            
            if not points_without_extraction:
                self.logger.info("No points found without extracted_entities field")
                return {
                    'success': True,
                    'message': 'No points need updating',
                    'processed_count': 0,
                    'updated_count': 0,
                    'failed_count': 0
                }
            
            self.logger.info(f"Found {len(points_without_extraction)} points without extracted_entities field")
            
            processed_count = 0
            updated_count = 0
            failed_count = 0
            
            for point in points_without_extraction:
                try:
                    processed_count += 1
                    
                    # Sleep for 0.5 seconds between processing each point
                    time.sleep(0.5)
                    
                    # Get the summary from the point
                    summary = point.get('summary')
                    if not summary:
                        self.logger.warning(f"Point {point.get('content_id', 'unknown')} has no summary field, skipping")
                        failed_count += 1
                        continue
                    
                    # Extract information from summary
                    self.logger.info(f"Processing point {processed_count}/{len(points_without_extraction)}: {point.get('content_id', 'unknown')}")
                    self.logger.info(f"Summary text: {summary}")
                    
                    info_result = self._extract_info_single_news(summary)
                    if not info_result['success']:
                        self.logger.warning(f"Failed to extract information for point {point.get('content_id', 'unknown')}")
                        failed_count += 1
                        continue
                    
                    extracted_entities = info_result['entities']
                    
                    # Update the point with extracted entities
                    if dry_run:
                        self.logger.info(f"🔍 DRY RUN: Would update point {point.get('content_id', 'unknown')} with {len(extracted_entities)} entity categories")
                        updated_count += 1
                        update_success = True
                    else:
                        update_success = self.storage.update_point_extracted_entities(
                            point.get('content_id'), 
                            extracted_entities
                        )
                        
                        if update_success:
                            updated_count += 1
                            self.logger.info(f"✅ Successfully updated point {point.get('content_id', 'unknown')} with {len(extracted_entities)} entity categories")
                        else:
                            failed_count += 1
                            self.logger.error(f"Failed to update point {point.get('content_id', 'unknown')} in database")
                    
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Exception processing point {point.get('content_id', 'unknown')}: {e}")
                    continue
            
            result = {
                'success': True,
                'message': f'Processed {processed_count} points, updated {updated_count}, failed {failed_count}' + (' (DRY RUN)' if dry_run else ''),
                'processed_count': processed_count,
                'updated_count': updated_count,
                'failed_count': failed_count,
                'dry_run': dry_run
            }
            
            self.logger.info(f"Update completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Exception during update_existing_points_with_extraction: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'processed_count': 0,
                'updated_count': 0,
                'failed_count': 0
            }
