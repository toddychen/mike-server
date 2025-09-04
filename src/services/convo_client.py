#!/usr/bin/env python3
"""
ConvoClient - A conversational AI client for sports game commentary
"""

import openai
import logging
import os
from typing import Dict, List, Any, Optional
from config.settings import settings


class ConvoClient:
    """Client for generating conversational responses about sports games"""
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize ConvoClient
        
        Args:
            model: GPT model to use (if None, uses default)
        """
        self.logger = logging.getLogger(__name__)
        
        # Ensure ConvoClient logger has the same level as the main logger
        main_logger = logging.getLogger("mike_server")
        self.logger.setLevel(main_logger.level)
        
        # Log that ConvoClient is initialized
        self.logger.info("ConvoClient logger initialized")
        
        # Get API key from settings or environment variable
        api_key = settings.openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in settings or environment variable.")
        
        # Set model
        if not model:
            model = "gpt-5-mini"  # Default model for conversational responses
        
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        self.logger.info(f"ConvoClient initialized with model: {self.model}")
    
    def generate_conversation_response(
        self,
        recent_play_text: str,
        latest_play: Dict[str, Any],
        related_news: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a conversational response based on play context and related news
        
        Args:
            recent_play_text: Text from LastXPlays field (recent play history)
            latest_play: Current play object with game stats and details
            related_news: List of related news articles
            
        Returns:
            Conversational response string or "[NO ACTION]" if not interesting
        """
        try:
            self.logger.info("=== ConvoClient: Starting to generate conversational response ===")
            self.logger.info("Generating conversational response for play")
            
            # Build the prompt
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_prompt(recent_play_text, latest_play, related_news)
            
            # Log the prompts
            self.logger.info(f"System prompt: {system_prompt}")
            self.logger.info(f"User prompt: {user_prompt}")
            
            # Call GPT API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": user_prompt
                    }
                ],
                max_completion_tokens=1000,  # Keep responses short (1-3 sentences) - increased to avoid truncation
            )
            
            # Log the complete response object for debugging
            self.logger.info(f"Complete GPT response object: {response}")
            
            # Extract and log token usage statistics
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', input_tokens + output_tokens)
                
                # Calculate pricing for GPT-5 mini
                input_cost = (input_tokens / 1_000_000) * 0.250  # $0.250 per 1M tokens
                output_cost = (output_tokens / 1_000_000) * 2.000  # $2.000 per 1M tokens
                total_cost = input_cost + output_cost
                
                self.logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
                self.logger.info(f"Cost calculation - Input: ${input_cost:.6f}, Output: ${output_cost:.6f}, Total: ${total_cost:.6f}")
            else:
                self.logger.warning("No token usage information available in response")
            
            result = response.choices[0].message.content.strip()
            self.logger.info(f"Generated response: {result}")
            
            # Wrap up the result with cost data
            convo_result = {
                "convo": result,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost
            }
            
            return convo_result
            
        except Exception as e:
            self.logger.error(f"Error generating conversation response: {e}")
            return {
                "convo": "[NO ACTION]",
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0
            }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the AI's role and behavior"""
        return """You are a knowledgeable sports fan watching an American football game live with me. 

Your personality:
- You're conversational, like talking to a close friend
- You have deep knowledge but act like a normal fan
- You use casual phrases, sports slang, and everyday language
- You get excited about good plays and react naturally
- You sometimes ask questions or share observations like any fan would

Your behavior:
- Before speaking, always decide whether the current play and news context are related and interesting
- If not interesting or not related, respond with exactly "[NO ACTION]"
- If you speak, keep it short (1-3 sentences) and natural
- Act like a normal fan who happens to know a lot about the game
- Be enthusiastic, casual, and relatable

Examples of good responses:
- "Wow, that's a huge play! Did you see how he broke that tackle? That was some serious power right there."
- "Man, this is getting intense! What do you think about that call? I'm not sure if I agree with the ref on that one."
- "That's a classic [team name] move right there! They always seem to pull this off when they need it most."
- "Dude, this reminds me of that play from last season when they did the exact same thing against the Packers."
- "Holy cow, did you see that? That was insane! I can't believe he made that catch with two defenders on him."
- "Man, I can't believe they called that. What do you think? That looked like a clean hit to me."
- "Wait, didn't they just trade that guy last week? Or am I thinking of someone else? This performance is making me question my memory."
- "Is this his first touchdown this season? I feel like he's been quiet lately, but maybe I just haven't been paying attention."
- "How many yards does that make for him today? I lost track after that big run in the second quarter."
- "Didn't I read somewhere that he was dealing with an injury? He looks fine to me out there, running like nothing's wrong."
- "Wasn't there some drama about his contract? This performance might change things if he keeps playing like this."
- "Am I crazy or did they use this exact play against us last year? It's like deja vu watching this."

Remember: Only respond if the play and news context are genuinely interesting and related. Otherwise, use "[NO ACTION]"."""
    
    def _build_prompt(
        self,
        recent_play_text: str,
        latest_play: Dict[str, Any],
        related_news: List[Dict[str, Any]]
    ) -> str:
        """Build the user prompt with context information"""
        
        # Extract key information from latest play
        period_display = latest_play.get("PeriodDisplayString", "Unknown")
        display_clock = latest_play.get("DisplayClock", "Unknown")
        home_score = latest_play.get("HomeScore", 0)
        away_score = latest_play.get("AwayScore", 0)
        down = latest_play.get("Down", "Unknown")
        yards_to_go = latest_play.get("YardsToGo", "Unknown")
        summary = latest_play.get("Summary", "Unknown")
        
        # Build current play description from stats
        current_play_description = f"{period_display} Quarter, {display_clock} - Score: {away_score}-{home_score}, {down} and {yards_to_go}, ({summary})"
        
        # Build news context
        news_context = ""
        if related_news:
            news_context = "Related News:\n"
            for i, news in enumerate(related_news[:5], 1):  # Limit to top 5 news
                summary = news.get("summary", "No summary")
                score = news.get("score", 0.0)
                news_context += f"{i}. (Relevance: {score:.2f})\n   {summary}\n\n"
        else:
            news_context = "No related news found.\n"
        
        prompt = f"""Recent Play History:
{recent_play_text}

Current Play:
{current_play_description}

News Context:
{news_context}

Based on this context, decide if there's something interesting to comment on. Consider:
1. Is the current play interesting or significant?
2. Is there a connection between the play and the related news?
3. Would a casual fan find this worth talking about?

If yes, respond naturally as a sports fan friend. If no, respond with "[NO ACTION]"."""
        
        return prompt
