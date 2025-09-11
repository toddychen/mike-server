from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.game_play_service import GamePlayService
from services.convo_client import ConvoClient
from datetime import datetime, timedelta
from utils.logger import logger
import traceback

router = APIRouter()
game_service = GamePlayService()
convo_client = ConvoClient()
logger.info("ConvoClient initialized in game router")

@router.get("/{game_id}/replay")
async def get_game_replay(
    game_id: str,
    start: str = Query(..., description="Game start timestamp (ISO format or 'YYYY-MM-DD HH:MM:SS')"),
    seconds_per_play: int = Query(30, description="Average seconds per play (default: 30)"),
    lastX: int = Query(3, description="Number of last plays to concatenate for LastXPlays field (default: 3)"),
    convo: bool = Query(False, description="Enable conversational AI responses (default: false)")
):
    """
    Get game replay data based on current time simulation
    
    Args:
        game_id: Game identifier (e.g., 'nfl.g.20250823025')
        start: Game start timestamp
        seconds_per_play: Average seconds per play
        lastX: Number of last plays to concatenate for LastXPlays field
        convo: Enable conversational AI responses
        
    Returns:
        JSON response containing replay data with truncated plays
    """
    try:
        # Get replay data
        replay_data = game_service.get_replay_plays(
            game_id=game_id,
            start_timestamp=start,
            seconds_per_play=seconds_per_play
        )
        
        # Extract current play details and search for related news
        try:
            current_play_count = replay_data.get("ReplayInfo", {}).get("CurrentPlayCount", 0)
            plays = replay_data.get("Plays", [])
            
            if plays:
                # Get current play object by index (last play in the truncated list)
                current_play = plays[-1]  # Last play in the truncated list is the current play
                
                if current_play:
                    # Build LastXPlays field by concatenating the last X plays' Details
                    last_x_plays_text = ""
                    if len(plays) >= lastX:
                        # Get the last X plays
                        last_x_plays = plays[-lastX:]
                        # Concatenate their Details fields
                        last_x_plays_text = ". ".join([play.get("Details", "") for play in last_x_plays])
                    else:
                        # If we have fewer plays than requested, use all available plays
                        last_x_plays_text = ". ".join([play.get("Details", "") for play in plays])
                    
                    # Add LastXPlays field to current play
                    current_play["LastXPlays"] = last_x_plays_text
                    
                    # Log current play details and LastXPlays
                    play_text = current_play.get("Details", "No details available")
                    logger.info(f"Current play text for game {game_id}: {play_text[:100]}...")
                    logger.info(f"LastXPlays text for game {game_id}: {last_x_plays_text[:100]}...")
                    
                    # Get related news using the LastXPlays text instead of just the current play text
                    try:
                        related_news = game_service.get_related_news_for_play(
                            play_text=last_x_plays_text,  # Use LastXPlays text instead of single play text
                            days_back=7,
                            top_k=10
                        )
                        
                        # Add RelatedNews field to current play
                        current_play["RelatedNews"] = related_news
                        
                        #logger.info(f"Added {len(related_news)} related news to LastXPlays text")
                        
                        # Generate conversational response only if convo is enabled
                        if convo:
                            logger.info("ConvoClient: convo=true, calling generate_conversation_response")
                            try:
                                convo_result = convo_client.generate_conversation_response(
                                    recent_play_text=last_x_plays_text,
                                    latest_play=current_play,
                                    related_news=related_news
                                )
                                
                                # Add conversation response and cost data to current play
                                current_play["ConvoResponse"] = convo_result["convo"]
                                current_play["InputCost"] = convo_result["input_cost"]
                                current_play["OutputCost"] = convo_result["output_cost"]
                                current_play["TotalCost"] = convo_result["total_cost"]
                                
                                logger.info(f"Generated conversational response: {convo_result['convo']}")
                                logger.info(f"Cost data - Input: ${convo_result['input_cost']:.6f}, Output: ${convo_result['output_cost']:.6f}, Total: ${convo_result['total_cost']:.6f}")
                            except Exception as e:
                                logger.warning(f"Failed to generate conversational response: {e}")
                                current_play["ConvoResponse"] = "[NO ACTION]"
                                current_play["InputCost"] = 0.0
                                current_play["OutputCost"] = 0.0
                                current_play["TotalCost"] = 0.0
                        else:
                            # If convo is disabled, don't add ConvoResponse field
                            logger.debug("Conversational responses disabled")
                        
                    except Exception as e:
                        logger.warning(f"Failed to get related news: {e}")
                        current_play["RelatedNews"] = []
                        if convo:
                            current_play["ConvoResponse"] = "[NO ACTION]"
                else:
                    logger.warning(f"No current play: {current_play_count}")
            else:
                logger.info(f"No current play to process (CurrentPlayCount: {current_play_count})")
                
        except Exception as e:
            logger.warning(f"Failed to process related news: {e}")
        
        # Reverse the Plays list so the latest plays appear first
        if "Plays" in replay_data and replay_data["Plays"]:
            replay_data["Plays"].reverse()
            # logger.info(f"Reversed Plays list order for game {game_id}")
        
        return replay_data
        
    except FileNotFoundError as e:
        logger.warning(f"Game data not found for {game_id}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Game data not found: {str(e)}"
        )
    except ValueError as e:
        logger.warning(f"Invalid parameters for game {game_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameters: {str(e)}"
        )
    except Exception as e:
        error_msg = f"Game replay failed for {game_id}: {e}"
        stack_trace = traceback.format_exc()
        
        # Log detailed error information
        logger.error(error_msg)
        logger.error(f"Error stack trace:\n{stack_trace}")
        
        # Return detailed error information
        raise HTTPException(
            status_code=500,
            detail=f"Replay failed: {str(e)}\nStack trace: {stack_trace}"
        )

@router.get("/{game_id}/plays")
async def get_game_plays(
    game_id: str,
    lastX: int = Query(3, description="Number of last plays to concatenate for LastXPlays field (default: 3)"),
    convo: bool = Query(False, description="Enable conversational AI responses (default: false)")
):
    """
    Get full game plays data for a specific game from API
    
    Args:
        game_id: Game identifier (e.g., 'nfl.g.20250823025')
        lastX: Number of last plays to concatenate for LastXPlays field
        convo: Enable conversational AI responses
        
    Returns:
        JSON response containing full game data with LastXPlays and optional conversation
    """
    try:
        # Get full game data from API (no local file)
        game_data = game_service.fetch_plays_from_api(game_id)
        
        # Extract plays and drives
        plays = game_data.get("Plays", [])
        drives = game_data.get("Drives", [])
        
        if plays:
            # Get the last play as current play
            current_play = plays[-1]  # Last play in the list is the current play
            
            if current_play:
                # Build LastXPlays field by concatenating the last X plays' Details
                last_x_plays_text = ""
                if len(plays) >= lastX:
                    # Get the last X plays
                    last_x_plays = plays[-lastX:]
                    # Concatenate their Details fields
                    last_x_plays_text = ". ".join([play.get("Details", "") for play in last_x_plays])
                else:
                    # If we have fewer plays than requested, use all available plays
                    last_x_plays_text = ". ".join([play.get("Details", "") for play in plays])
                
                # Add LastXPlays field to current play
                current_play["LastXPlays"] = last_x_plays_text
                
                # Log current play details and LastXPlays
                play_text = current_play.get("Details", "No details available")
                logger.info(f"Current play text for game {game_id}: {play_text[:100]}...")
                logger.info(f"LastXPlays text for game {game_id}: {last_x_plays_text[:100]}...")
                
                # Get related news using the LastXPlays text
                try:
                    related_news = game_service.get_related_news_for_play(
                        play_text=last_x_plays_text,  # Use LastXPlays text
                        days_back=7,
                        top_k=10
                    )
                    
                    # Add RelatedNews field to current play
                    current_play["RelatedNews"] = related_news
                    
                    # Generate conversational response only if convo is enabled
                    if convo:
                        logger.info("ConvoClient: convo=true, calling generate_conversation_response")
                        try:
                            convo_result = convo_client.generate_conversation_response(
                                recent_play_text=last_x_plays_text,
                                latest_play=current_play,
                                related_news=related_news
                            )
                            
                            # Add conversation response and cost data to current play
                            current_play["ConvoResponse"] = convo_result["convo"]
                            current_play["InputCost"] = convo_result["input_cost"]
                            current_play["OutputCost"] = convo_result["output_cost"]
                            current_play["TotalCost"] = convo_result["total_cost"]
                            
                            logger.info(f"Generated conversational response: {convo_result['convo']}")
                            logger.info(f"Cost data - Input: ${convo_result['input_cost']:.6f}, Output: ${convo_result['output_cost']:.6f}, Total: ${convo_result['total_cost']:.6f}")
                        except Exception as e:
                            logger.warning(f"Failed to generate conversational response: {e}")
                            current_play["ConvoResponse"] = "[NO ACTION]"
                            current_play["InputCost"] = 0.0
                            current_play["OutputCost"] = 0.0
                            current_play["TotalCost"] = 0.0
                    else:
                        # If convo is disabled, don't add ConvoResponse field
                        logger.debug("Conversational responses disabled")
                    
                except Exception as e:
                    logger.warning(f"Failed to get related news: {e}")
                    current_play["RelatedNews"] = []
                    if convo:
                        current_play["ConvoResponse"] = "[NO ACTION]"
            else:
                logger.warning(f"No current play found")
        else:
            logger.info(f"No plays found in game data")
        
        # Reverse the Plays list so the latest plays appear first
        if "Plays" in game_data and game_data["Plays"]:
            game_data["Plays"].reverse()
        
        return game_data
        
    except ValueError as e:
        logger.warning(f"Invalid parameters for game {game_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameters: {str(e)}"
        )
    except Exception as e:
        error_msg = f"Failed to get game plays for {game_id}: {e}"
        stack_trace = traceback.format_exc()
        
        logger.error(error_msg)
        logger.error(f"Error stack trace:\n{stack_trace}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get game plays: {str(e)}\nStack trace: {stack_trace}"
        )
