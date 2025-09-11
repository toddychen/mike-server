from typing import Dict, Any
from function_calling.function_registry import function_registry
from function_calling.yahoo_sports_client import YahooSportsClient
from function_calling.sports_functions import SportsFunctions
from models.function_calls import FunctionMetadata
from utils.web_client import WebClient
from utils.logger import logger

# Global instances
web_client = WebClient()
yahoo_sports_client = YahooSportsClient(web_client)
sports_functions = SportsFunctions(yahoo_sports_client)

def register_yahoo_sports_functions():
    """Register all Yahoo Sports related functions"""
    
    # Register search entity function
    function_registry.register(
        name="search_entity",
        func=sports_functions.search_entity,
        metadata=FunctionMetadata(
            name="search_entity",
            description="Search for sports entities (players, teams, leagues) to find their IDs. Use this function first to get entity IDs, then use those IDs in other functions that require specific entity IDs.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "Search query for entity (e.g., 'LeBron James', 'Lakers', 'NFL')"
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Optional filter by entity type to narrow down search results",
                        "enum": ["player", "team", "league"]
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            required_parameters=["query"],
            optional_parameters=["entity_type"],
            return_type="dict",
            timeout_seconds=10,
            rate_limit_per_minute=30,
            tags=["search", "sports", "yahoo"],
            external_api_url="https://mrest.sports.yahoo.com/api/v8/search"
        )
    )
    
    # Register get league games function
    function_registry.register(
        name="get_league_games",
        func=sports_functions.get_league_games,
        metadata=FunctionMetadata(
            name="get_league_games",
            description="Get games for specified league(s)",
            parameters={
                "type": "object",
                "properties": {
                    "leagues": {
                        "type": "string", 
                        "description": "League name(s) (e.g., 'nfl', 'nba')"
                    },
                    "count": {
                        "type": "integer", 
                        "description": "Number of games to return",
                        "minimum": 1,
                        "maximum": 100
                    },
                    "dates": {
                        "type": "string", 
                        "description": "Date range for games in ISO8601 format (yyyy-MM-DD), or leave blank for CURRENT date"
                    },
                    "weeks": {
                        "type": "string", 
                        "description": "Week range for weekly-based sports (NFL, NCAAF, CFL), or leave blank for CURRENT date"
                    },
                    "season": {
                        "type": "string", 
                        "description": "Season for games, or leave blank for CURRENT season"
                    }
                },
                "required": ["leagues"],
                "additionalProperties": False
            },
            required_parameters=["leagues"],
            optional_parameters=["count", "dates", "weeks", "season"],
            return_type="dict",
            timeout_seconds=15,
            rate_limit_per_minute=20,
            tags=["games", "league", "yahoo"],
            external_api_url="https://graphite.sports.yahoo.com/v1/query/genAI/leagueGames"
        )
    )
    
    # Register get team games function
    function_registry.register(
        name="get_team_games",
        func=sports_functions.get_team_games,
        metadata=FunctionMetadata(
            name="get_team_games",
            description="Get games for a specific team. Requires team_id which can be obtained from search_entity function.",
            parameters={
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string", 
                        "description": "Team ID obtained from search_entity function (e.g., 'nfl.t.9', 'nba.t.13')"
                    },
                    "season": {
                        "type": "string", 
                        "description": "Season for games, or leave blank for CURRENT season"
                    }
                },
                "required": ["team_id"],
                "additionalProperties": False
            },
            required_parameters=["team_id"],
            optional_parameters=["season"],
            return_type="dict",
            timeout_seconds=15,
            rate_limit_per_minute=20,
            tags=["games", "team", "yahoo"],
            external_api_url="https://graphite.sports.yahoo.com/v1/query/genAI/teamGames"
        )
    )
    
    logger.info("Yahoo Sports functions registered successfully")

def register_all_functions():
    """Register all available functions"""
    # Register Yahoo Sports functions
    register_yahoo_sports_functions()
    
    # Future: Add more function categories here
    # register_espn_functions()
    # register_nfl_functions()
    
    logger.info("All functions registered successfully")

async def cleanup_web_client():
    """Cleanup web client resources"""
    await web_client.close()
