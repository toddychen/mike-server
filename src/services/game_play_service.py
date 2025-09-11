#!/usr/bin/env python3
"""
Game Play Service for fetching and caching NFL game play data
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Any
import requests
from requests.exceptions import RequestException

from models.news import NewsSearchQuery


class GamePlayService:
    """Service for managing NFL game play data with local caching"""
    
    # Class-level logger
    logger = logging.getLogger(__name__)
    
    def __init__(self, base_url: str = "https://mrest.sports.yahoo.com/api/v8/game"):
        """
        Initialize GamePlayService
        
        Args:
            base_url: Base URL for the Yahoo Sports API
        """
        self.base_url = base_url.rstrip('/')
        self.data_dir = Path("data/game_plays")
        self._ensure_data_directory()
        
        # Initialize dependent services
        from services.news_storage import NewsStorage
        from services.information_extractor import InformationExtractor
        from services.entity_similarity import EntitySimilarityService
        
        self.news_storage = NewsStorage()
        self.information_extractor = InformationExtractor()
        self.entity_similarity_service = EntitySimilarityService()
        
        self.logger.info(f"GamePlayService initialized with base URL: {self.base_url}")
        self.logger.info(f"Data directory: {self.data_dir}")
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Data directory ensured: {self.data_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create data directory {self.data_dir}: {e}")
            raise
    
    def get_plays(self, game_id: str) -> Dict:
        """
        Get game plays data, either from local cache or by fetching from API
        
        Args:
            game_id: Game identifier (e.g., 'nfl.g.20250823025')
            
        Returns:
            Dictionary containing the game plays data
            
        Raises:
            ValueError: If game_id is invalid
            RequestException: If API request fails
            Exception: For other errors during processing
        """
        if not game_id or not isinstance(game_id, str):
            raise ValueError("game_id must be a non-empty string")
        
        self.logger.info(f"Getting plays for game: {game_id}")
        
        # Check if local file exists
        local_file_path = self.data_dir / f"{game_id}.json"
        
        if local_file_path.exists():
            self.logger.info(f"Found local cache file: {local_file_path}")
            return self._load_local_file(local_file_path)
        
        self.logger.info(f"No local cache found, fetching from API...")
        return self._fetch_and_save_plays(game_id, local_file_path)
    
    def _load_local_file(self, file_path: Path) -> Dict:
        """Load data from local JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"Successfully loaded local file: {file_path}")
                return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse local JSON file {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load local file {file_path}: {e}")
            raise
    
    def _fetch_and_save_plays(self, game_id: str, local_file_path: Path) -> Dict:
        """Fetch plays from API and save to local file"""
        try:
            # Construct API URL
            api_url = f"{self.base_url}/{game_id}/periodGamePlays"
            self.logger.info(f"Fetching from API: {api_url}")
            
            # Make HTTP request
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON response
            raw_data = response.json()
            self.logger.info(f"Successfully fetched data from API, response size: {len(response.text)} characters")
            
            # Post-process the data (dummy method for now)
            processed_data = self._post_process_data(raw_data)
            
            # Save to local file
            self._save_to_local_file(local_file_path, processed_data)
            
            self.logger.info(f"Successfully saved processed data to: {local_file_path}")
            return processed_data
            
        except RequestException as e:
            self.logger.error(f"HTTP request failed for game {game_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response JSON for game {game_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching plays for game {game_id}: {e}")
            raise
    
    def fetch_plays_from_api(self, game_id: str) -> Dict:
        """
        Fetch plays from API without saving to local file
        
        Args:
            game_id: Game identifier (e.g., 'nfl.g.20250823025')
            
        Returns:
            Dictionary containing the processed game plays data
            
        Raises:
            ValueError: If game_id is invalid
            RequestException: If API request fails
            Exception: For other errors during processing
        """
        if not game_id or not isinstance(game_id, str):
            raise ValueError("game_id must be a non-empty string")
        
        try:
            # Construct API URL
            api_url = f"{self.base_url}/{game_id}/periodGamePlays"
            self.logger.info(f"Fetching plays from API (no save): {api_url}")
            
            # Make HTTP request
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON response
            raw_data = response.json()
            self.logger.info(f"Successfully fetched data from API, response size: {len(response.text)} characters")
            
            # Post-process the data
            processed_data = self._post_process_data(raw_data)
            
            self.logger.info(f"Successfully processed data from API for game {game_id}")
            return processed_data
            
        except RequestException as e:
            self.logger.error(f"HTTP request failed for game {game_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response JSON for game {game_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching plays for game {game_id}: {e}")
            raise
    
    def _post_process_data(self, raw_data: Dict) -> Dict:
        """
        Post-process the raw API response data
        
        Args:
            raw_data: Raw JSON data from the API
            
        Returns:
            Processed data with simplified structure
        """
        try:
            self.logger.debug("Starting post-processing of API response data")
            
            # Create new structure
            processed_data = {
                "Drives": raw_data.get("Drives", []),
                "Plays": []
            }
            
            # Extract plays from PlaysByPeriod and flatten into simple list
            plays_by_period = raw_data.get("PlaysByPeriod", [])
            
            for period in plays_by_period:
                period_data = period.get("PeriodData", [])
                for play in period_data:
                    # Keep original PlayId as string, add PlayIdInt for sorting
                    play_id_str = play.get("PlayId", "0")
                    try:
                        play_id_int = int(play_id_str)
                        play["PlayIdInt"] = play_id_int
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid PlayId format: {play_id_str}, setting PlayIdInt to 0")
                        play["PlayIdInt"] = 0
                    
                    processed_data["Plays"].append(play)
            
            # Sort plays by PlayIdInt from smallest to largest
            try:
                processed_data["Plays"].sort(key=lambda x: x.get("PlayIdInt", 0))
                self.logger.info(f"Successfully sorted {len(processed_data['Plays'])} plays by PlayIdInt")
            except Exception as e:
                self.logger.warning(f"Failed to sort plays by PlayIdInt: {e}")
            
            # Log processing summary
            drives_count = len(processed_data["Drives"])
            plays_count = len(processed_data["Plays"])
            self.logger.info(f"Post-processing completed: {drives_count} drives, {plays_count} plays")
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error during post-processing: {e}")
            # Return original data if processing fails
            return raw_data
    
    def _save_to_local_file(self, file_path: Path, data: Dict):
        """Save data to local JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Data saved to local file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save data to local file {file_path}: {e}")
            raise
    
    def get_cache_info(self) -> Dict:
        """Get information about cached game files"""
        try:
            cache_files = list(self.data_dir.glob("*.json"))
            cache_info = {
                "total_files": len(cache_files),
                "data_directory": str(self.data_dir),
                "cached_games": [f.stem for f in cache_files],
                "total_size_mb": sum(f.stat().st_size for f in cache_files) / (1024 * 1024)
            }
            
            self.logger.info(f"Cache info: {cache_info['total_files']} files, "
                           f"{cache_info['total_size_mb']:.2f} MB total")
            return cache_info
            
        except Exception as e:
            self.logger.error(f"Failed to get cache info: {e}")
            raise
    
    def clear_cache(self, game_id: Optional[str] = None):
        """
        Clear cache - either specific game or all games
        
        Args:
            game_id: Specific game ID to clear, or None to clear all
        """
        try:
            if game_id:
                # Clear specific game
                file_path = self.data_dir / f"{game_id}.json"
                if file_path.exists():
                    file_path.unlink()
                    self.logger.info(f"Cleared cache for game: {game_id}")
                else:
                    self.logger.warning(f"No cache file found for game: {game_id}")
            else:
                # Clear all games
                cache_files = list(self.data_dir.glob("*.json"))
                for file_path in cache_files:
                    file_path.unlink()
                self.logger.info(f"Cleared all cache files: {len(cache_files)} files removed")
                
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            raise
    
    def get_replay_plays(self, game_id: str, start_timestamp: str, seconds_per_play: int = 30) -> Dict:
        """
        Get plays data for replay simulation based on current time
        
        Args:
            game_id: Game identifier (e.g., 'nfl.g.20250823025')
            start_timestamp: Game start time in ISO format (e.g., '2025-08-23T19:00:00Z')
            seconds_per_play: Average seconds per play (default: 30)
            
        Returns:
            Dictionary containing replay data with truncated plays based on time simulation
            
        Raises:
            ValueError: If game_id is invalid or start_timestamp is invalid
            FileNotFoundError: If game data file doesn't exist
            Exception: For other errors during processing
        """
        if not game_id or not isinstance(game_id, str):
            raise ValueError("game_id must be a non-empty string")
        
        if not start_timestamp or not isinstance(start_timestamp, str):
            raise ValueError("start_timestamp must be a non-empty string")
        
        if seconds_per_play <= 0:
            raise ValueError("seconds_per_play must be positive")
        
        self.logger.info(f"Getting replay plays for game: {game_id}")
        self.logger.info(f"Start timestamp: {start_timestamp}, Seconds per play: {seconds_per_play}")
        
        # Check if local file exists
        local_file_path = self.data_dir / f"{game_id}.json"
        if not local_file_path.exists():
            raise FileNotFoundError(f"Game data file not found: {local_file_path}")
        
        try:
            # Load game data
            game_data = self._load_local_file(local_file_path)
            
            # Parse start timestamp to Unix timestamp
            try:
                if start_timestamp.isdigit():
                    # If it's already a Unix timestamp
                    start_timestamp_long = int(start_timestamp)
                else:
                    # Parse datetime string to Unix timestamp
                    try:
                        start_time = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        # Try alternative format
                        start_time = datetime.strptime(start_timestamp, '%Y-%m-%d %H:%M:%S')
                    
                    # Convert to Unix timestamp
                    start_timestamp_long = int(start_time.timestamp())
            except Exception as e:
                raise ValueError(f"Invalid start timestamp format: {start_timestamp}. Use Unix timestamp (e.g., 1692835200) or ISO format")
            
            current_time = datetime.now()
            current_timestamp_long = int(current_time.timestamp())
            
            # Calculate replay progress using timestamps
            elapsed_seconds = current_timestamp_long - start_timestamp_long
            if elapsed_seconds < 0:
                self.logger.warning(f"Start time is in the future, treating as game not started")
                elapsed_seconds = 0
            
            expected_plays = int(elapsed_seconds / seconds_per_play)
            
            # Get plays and drives
            plays = game_data.get("Plays", [])
            drives = game_data.get("Drives", [])
            
            if not plays:
                self.logger.warning(f"No plays found in game data")
                return self._create_replay_response([], drives, start_timestamp, current_time, seconds_per_play, 0, 0, 0, "NOT_STARTED")
            
            # Use total play count instead of max_play_id
            total_play_count = len(plays)
            current_play_count = min(expected_plays, total_play_count)
            
            # Determine status and filter plays by index
            if current_play_count >= total_play_count:
                status = "FINAL"
                progress_percentage = 100.0
                truncated_plays = plays
                self.logger.info(f"Game finished, showing all {total_play_count} plays")
            else:
                status = "LIVE"
                progress_percentage = (current_play_count / total_play_count) * 100
                
                # Get plays up to current play index
                truncated_plays = plays[:current_play_count]
                
                self.logger.info(f"Game in progress, showing {len(truncated_plays)} of {total_play_count} plays ({progress_percentage:.1f}%)")
            
            # Create replay response
            replay_data = self._create_replay_response(
                truncated_plays, drives, start_timestamp, current_time,
                seconds_per_play, current_play_count, total_play_count, progress_percentage, status
            )
            
            return replay_data
            
        except Exception as e:
            self.logger.error(f"Error during replay processing: {e}")
            raise
    
    def _create_replay_response(self, plays: List[Dict], drives: List[Dict], start_timestamp: str, 
                               current_time: datetime, seconds_per_play: int, current_play_count: int, 
                               total_play_count: int, progress_percentage: float, status: str) -> Dict[str, Any]:
        """
        Create the replay response structure with cleaned input parameters and consistent output keys
        
        Args:
            plays: List of play data dictionaries
            drives: List of drive data dictionaries  
            start_timestamp: Game start timestamp (Unix timestamp or ISO format string)
            current_time: Current datetime object
            seconds_per_play: Average seconds per play
            current_play_count: Current number of plays shown (0-based index)
            total_play_count: Total number of plays in the game
            progress_percentage: Game progress percentage (0-100)
            status: Game status (e.g., "LIVE", "FINAL")
            
        Returns:
            Dictionary containing replay data with consistent key structure
        """
        # Validate input parameters
        if not isinstance(plays, list):
            plays = []
        if not isinstance(drives, list):
            drives = []
        if not isinstance(current_time, datetime):
            current_time = datetime.now()
        
        # Convert timestamps to ISO format for consistency
        start_iso = self._normalize_timestamp(start_timestamp)
        current_iso = current_time.isoformat() + 'Z'
        
        # Calculate elapsed seconds using timestamps
        elapsed_seconds = self._calculate_elapsed_seconds(start_timestamp, current_time)
        
        # Return structured response with consistent key naming
        return {
            "ReplayInfo": {
                "GameStatus": status,
                "CurrentPlayCount": current_play_count,
                "TotalPlayCount": total_play_count,
                "ProgressPercentage": round(progress_percentage, 1),
                "ElapsedSeconds": elapsed_seconds,
                "SecondsPerPlay": seconds_per_play,
                "GameStartTime": start_iso,
                "CurrentTime": current_iso
            },
            "Plays": plays,
            "Drives": drives
        }
    
    def _normalize_timestamp(self, timestamp: str) -> str:
        """Normalize timestamp to ISO format"""
        if not timestamp:
            return datetime.now().isoformat() + 'Z'
        
        if 'T' in timestamp:
            # Already in ISO format
            return timestamp if timestamp.endswith('Z') else timestamp + 'Z'
        else:
            # Convert space-separated format to ISO
            return timestamp.replace(' ', 'T') + 'Z'
    
    def _calculate_elapsed_seconds(self, start_timestamp: str, current_time: datetime) -> int:
        """Calculate elapsed seconds between start timestamp and current time"""
        try:
            if start_timestamp.isdigit():
                # If it's already a Unix timestamp
                start_timestamp_long = int(start_timestamp)
            else:
                # Parse datetime string to Unix timestamp
                try:
                    start_time = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    # Try alternative format
                    start_time = datetime.strptime(start_timestamp, '%Y-%m-%d %H:%M:%S')
                start_timestamp_long = int(start_time.timestamp())
            
            current_timestamp_long = int(current_time.timestamp())
            elapsed_seconds = current_timestamp_long - start_timestamp_long
            
            # Ensure non-negative elapsed time
            return max(0, elapsed_seconds)
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate elapsed seconds: {e}")
            return 0
    
    def get_related_news_for_play(self, play_text: str, days_back: int = 7, top_k: int = 10) -> List[Dict]:
        """
        Get related news for a specific play with entity similarity calculation
        
        Args:
            play_text: The play description text
            days_back: Number of days back to search for news
            top_k: Number of top related news to return
            
        Returns:
            List of formatted news objects with entity similarity scores
        """
        try:
            self.logger.info(f"Getting related news for play: {play_text[:100]}...")
            
            # Extract entities from play text
            play_entities = []
            try:
                play_entities_result = self.information_extractor.extract_entities(play_text)
                play_entities = self.information_extractor.convert_entities_to_list(play_entities_result.entities)
                self.logger.info(f"Extracted {len(play_entities)} entities from play text")
            except Exception as e:
                self.logger.warning(f"Exception during entity extraction: {e}")
            
            # Search for related news using semantic search
            try:
                # Create search query for recent news
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days_back)
                
                search_query = NewsSearchQuery(
                    query_text=play_text,
                    before=end_time,
                    after=start_time,
                    top_k=top_k
                )
                
                related_news = self.news_storage.search_similar_news(search_query)
                
                # Format related news with entity similarity
                formatted_news = []
                for news in related_news:
                    summary = news.get("summary", "")
                    
                    # Calculate entity similarity if we have play entities
                    entity_similarity = None
                    if play_entities:
                        try:
                            # Get extracted entities from news
                            news_extracted_entities = news.get("extracted_entities", {})
                            if news_extracted_entities:
                                # Convert news entities to list format for similarity calculation
                                news_entities = self.information_extractor.convert_db_entities_to_list(news_extracted_entities)
                                
                                # Calculate entity similarity
                                similarity_result = self.entity_similarity_service.weighted_containment_similarity(
                                    play_entities, 
                                    news_entities
                                )
                                entity_similarity = similarity_result
                            else:
                                entity_similarity = {
                                    'score': 0.0,
                                    'play_entity_count': len(play_entities),
                                    'news_entity_count': 0,
                                    'matched_count': 0
                                }
                        except Exception as e:
                            self.logger.warning(f"Failed to calculate entity similarity: {e}")
                            entity_similarity = {
                                'score': 0.0,
                                'play_entity_count': len(play_entities),
                                'news_entity_count': 0,
                                'matched_count': 0
                            }
                    
                    formatted_news.append({
                        "title": news.get("title", "No title"),
                        "summary": summary,
                        "score": news.get("score", 0.0),  # Semantic similarity score
                        "entity_similarity": entity_similarity  # Entity similarity score
                    })
                
                self.logger.info(f"Found {len(formatted_news)} related news with entity similarity")
                return formatted_news
                
            except Exception as e:
                self.logger.warning(f"Failed to search related news: {e}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting related news for play: {e}")
            return []
