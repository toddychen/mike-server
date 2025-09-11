from typing import Dict, Any, List
from utils.web_client import WebClient
from utils.logger import logger

class YahooSportsClient:
    """Client for Yahoo Sports API calls"""
    
    # Base URLs for different Yahoo Sports API endpoints
    MREST_BASE_PATH = "https://mrest.sports.yahoo.com/api/v8"
    GRAPHITE_BASE_PATH = "https://graphite.sports.yahoo.com/v1/query"
    
    # Complete URL paths for each API call
    PATHS = {
        "search": f"{MREST_BASE_PATH}/search",
        "league_games": f"{GRAPHITE_BASE_PATH}/genAI/leagueGames",
        "team_games": f"{GRAPHITE_BASE_PATH}/genAI/teamGames"
    }
    
    def __init__(self, web_client: WebClient):
        self.web_client = web_client
    
    async def search_entity(self, query: str) -> List[Dict[str, Any]]:
        """Search for sports entities (players, teams, etc.)"""
        try:
            logger.info(f"Searching for entity: {query}")
            result = await self.web_client.get(
                url=self.PATHS["search"],
                params={"text": query}
            )
            logger.info(f"Entity search successful for: {query}")
            return result
        except Exception as e:
            logger.error(f"Entity search failed for '{query}': {e}")
            raise
    
    async def get_league_games(self, leagues: str, count: int = 20, 
                              dates: str = "CURRENT", weeks: str = "CURRENT", 
                              season: str = "CURRENT") -> Dict[str, Any]:
        """Get games for specified league(s)"""
        try:
            logger.info(f"Fetching league games for: {leagues}")
            result = await self.web_client.get(
                url=self.PATHS["league_games"],
                params={
                    "leagues": leagues,
                    "count": count,
                    "dates": dates,
                    "weeks": weeks,
                    "season": season
                }
            )
            logger.info(f"League games fetch successful for: {leagues}")
            return result
        except Exception as e:
            logger.error(f"League games fetch failed for '{leagues}': {e}")
            raise
    
    async def get_team_games(self, team_id: str, season: str = "CURRENT") -> Dict[str, Any]:
        """Get games for specified team"""
        try:
            logger.info(f"Fetching team games for: {team_id}")
            result = await self.web_client.get(
                url=self.PATHS["team_games"],
                params={
                    "teamId": team_id,
                    "season": season
                }
            )
            logger.info(f"Team games fetch successful for: {team_id}")
            return result
        except Exception as e:
            logger.error(f"Team games fetch failed for '{team_id}': {e}")
            raise
