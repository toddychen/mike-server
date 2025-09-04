import logging
import re
import os
from typing import Optional, Dict, Any
from openai import OpenAI
from config.settings import settings

class NewsSummarizer:
    """Remote GPT API summarization service"""
        
    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        api_key = settings.openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in settings or environment variable.")
        
        if not model:
            model = settings.summarizer_model
        
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.logger.info(f"Initialized GPT API summarizer with model: {model}")
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        if not text:
            return 1
        return len(text.split())
    
    def _create_summary_prompt(self, text: str) -> str:
        """Create optimized prompt for summarization"""
        return f"""Summarize the following news article in 100-150 words:

{text}

Summary:"""
    
    def summarize(self, text: str) -> Dict[str, Any]:
        """Summarize text using GPT API"""
        if not text or self._count_words(text) < 150:
            return {
                'success': True,
                'summary': text if text else '',
                'summary_word_count': self._count_words(text) if text else 0,
                'method': 'no_change'
            }
        
        try:
            # Create prompt
            prompt = self._create_summary_prompt(text)
            
            input_word_count = self._count_words(text)
            self.logger.info(f"📜 Input text: {text}")
            self.logger.info(f"💹 Input stats: {self._count_words(text)} words")
            
            # Make API call using OpenAI client with Responses API
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=800,
                reasoning={"effort": "low"} 
            )

            # self.logger.info(f"Response: {response}")

            # Extract summary and usage
            summary = response.output_text

            usage = response.usage
            actual_input_tokens = usage.input_tokens
            actual_output_tokens = usage.output_tokens
            word_count = self._count_words(summary)
            
            self.logger.info(f"📜 Summary text: {summary}")
            self.logger.info(f"💹 Summary stats: {word_count} words.")
            self.logger.info(f"💹 Token stats: input={actual_input_tokens} tokens, output={actual_output_tokens} tokens")

            return {
                'success': True,
                'summary': summary,
                'summary_word_count': word_count,
                'original_word_count': input_word_count,
                'compression_ratio': round(word_count / input_word_count, 2),
                'method': 'gpt_api',
                'model': self.model,
                'tokens_used': {
                    'input': actual_input_tokens,
                    'output': actual_output_tokens,
                    'total': actual_input_tokens + actual_output_tokens
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during GPT summarization: {e}")
            return {
                'success': False,
                'error': str(e),
                'summary': '',
                'summary_word_count': 0,
                'method': 'gpt_api'
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the GPT model"""
        return {
            'model': self.model,
            'method': 'gpt_api',
            'provider': 'OpenAI'
        }
    
    def change_model(self, new_model: str):
        """Change the GPT model"""
        self.model = new_model
        self.logger.info(f"Changed GPT model to: {new_model}")

