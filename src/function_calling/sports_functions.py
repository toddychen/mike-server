from typing import Dict, Any, List, Optional
from function_calling.yahoo_sports_client import YahooSportsClient
from utils.logger import logger

class SportsFunctions:
    """Business logic functions for sports data processing and API integration"""
    
    def __init__(self, yahoo_client: YahooSportsClient):
        self.yahoo_client = yahoo_client
    
    async def search_entity(self, query: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Search for sports entities with filtering and truncation
        
        Args:
            query: Search query for entity
            entity_type: Optional filter by entity type ("player", "team", "league")
            
        Returns:
            Processed search results with categorized entities
        """
        try:
            logger.info(f"Searching for sports entity: {query} (type: {entity_type or 'all'})")
            
            # Get raw data from Yahoo Sports (returns list of entity objects)
            raw_data = await self.yahoo_client.search_entity(query)
            
            # Process and categorize the results with filtering and truncation
            processed_data = self._process_search_results(raw_data, entity_type)
            
            total_entities = sum(len(category) for category in processed_data.values() if isinstance(category, list))
            logger.info(f"Search completed for '{query}': {total_entities} entities found")
            return processed_data
            
        except Exception as e:
            logger.error(f"Sports entity search failed for '{query}': {e}")
            raise
    
    async def get_league_games(self, leagues: str, count: int = 20, 
                              dates: str = "CURRENT", weeks: str = "CURRENT", 
                              season: str = "CURRENT") -> Dict[str, Any]:
        """Get league games (pass-through to Yahoo Sports API)
        
        Args:
            leagues: League name(s) (e.g., 'nfl', 'nba')
            count: Number of games to return
            dates: Date range for games
            weeks: Week range for games
            season: Season for games
            
        Returns:
            Raw league games data from Yahoo Sports
        """
        try:
            logger.info(f"Fetching league games for: {leagues}")
            
            # Get raw data from Yahoo Sports and extract the "data" field
            response = await self.yahoo_client.get_league_games(
                leagues=leagues, count=count, dates=dates, 
                weeks=weeks, season=season
            )
            
            # Extract the "data" field from the response
            data = response.get("data", response)
            
            logger.info(f"League games fetch successful for: {leagues}")
            return data
            
        except Exception as e:
            logger.error(f"League games fetch failed for '{leagues}': {e}")
            raise
    
    async def get_team_games(self, team_id: str, season: str = "CURRENT") -> Dict[str, Any]:
        """Get team games (pass-through to Yahoo Sports API)
        
        Args:
            team_id: Team ID (e.g., 'nfl.t.9')
            season: Season for games
            
        Returns:
            Raw team games data from Yahoo Sports
        """
        try:
            logger.info(f"Fetching team games for: {team_id}")
            
            # Get raw data from Yahoo Sports and extract the "data" field
            response = await self.yahoo_client.get_team_games(team_id, season)
            
            # Extract the "data" field from the response
            data = response.get("data", response)
            
            logger.info(f"Team games fetch successful for: {team_id}")
            return data
            
        except Exception as e:
            logger.error(f"Team games fetch failed for '{team_id}': {e}")
            raise
    
    def _process_search_results(self, raw_data: List[Dict[str, Any]], entity_type_filter: Optional[str] = None) -> Dict[str, Any]:
        """Process and categorize search results with filtering and truncation
        
        Args:
            raw_data: Raw search results from Yahoo Sports (list of entity objects)
            entity_type_filter: Optional filter by entity type ("player", "team", "league")
            
        Returns:
            Processed results with categorized entities
        """
        try:
            # raw_data is already a list of entity objects
            results = raw_data
            
            # Filter by entity type if specified
            if entity_type_filter:
                entity_type_filter = entity_type_filter.lower()
                filtered_results = [
                    entity for entity in results 
                    if entity.get("Sddocname", "").lower() == entity_type_filter
                ]
                results = filtered_results
            
            # Categorize entities by type
            categorized = {
                "players": [],
                "teams": [],
                "leagues": []
            }
            
            for entity in results:
                entity_type = entity.get("Sddocname", "").lower()
                
                if entity_type == "player":
                    processed_player = self._process_player_entity(entity)
                    categorized["players"].append(processed_player)
                elif entity_type == "team":
                    processed_team = self._process_team_entity(entity)
                    categorized["teams"].append(processed_team)
                elif entity_type == "league":
                    processed_league = self._process_league_entity(entity)
                    categorized["leagues"].append(processed_league)
            
            # Apply truncation based on whether entity_type_filter was provided
            if entity_type_filter:
                # If filtering by specific type, truncate to top 2 results
                max_results = 2
                for category in ["players", "teams", "leagues"]:
                    if categorized[category]:
                        categorized[category] = categorized[category][:max_results]
            else:
                # If no filter, truncate to top 3 results total
                max_results = 3
                all_entities = []
                for category in ["players", "teams", "leagues"]:
                    all_entities.extend(categorized[category])
                
                # Take top 3 and redistribute
                top_entities = all_entities[:max_results]
                categorized = {
                    "players": [e for e in top_entities if e.get("type") == "player"],
                    "teams": [e for e in top_entities if e.get("type") == "team"],
                    "leagues": [e for e in top_entities if e.get("type") == "league"]
                }
            
            return categorized
            
        except Exception as e:
            logger.error(f"Failed to process search results: {e}")
            return {
                "success": False,
                "error": f"Failed to process search results: {str(e)}"
            }
    
    def _process_player_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Process a player entity from search results
        
        Args:
            entity: Raw player entity data
            
        Returns:
            Processed player data with essential fields only
        """
        return {
            "id": entity.get("Id"),
            "name": entity.get("DisplayName"),
            "primary_league": entity.get("PrimaryLeague"),
            "primary_team_id": entity.get("PrimaryTeam"),
            "primary_team_name": entity.get("PrimaryTeamDisplayName"),
            "type": "player"
        }
    
    def _process_team_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Process a team entity from search results
        
        Args:
            entity: Raw team entity data
            
        Returns:
            Processed team data with essential fields only
        """
        return {
            "id": entity.get("Id"),
            "name": entity.get("DisplayName"),
            "abbr": entity.get("Abbreviation"),
            "primary_league": entity.get("PrimaryLeague"),
            "type": "team"
        }
    
    def _process_league_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Process a league entity from search results
        
        Args:
            entity: Raw league entity data
            
        Returns:
            Processed league data with essential fields only
        """
        return {
            "id": entity.get("Id"),
            "name": entity.get("DisplayName"),
            "abbr": entity.get("Abbreviation"),
            "type": "league"
        }
    
