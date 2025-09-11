import httpx
import asyncio
from typing import Dict, Any, Optional
from utils.logger import logger

class WebClient:
    """Async client for making HTTP API calls with retry logic and realistic User-Agent"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Default realistic browser User-Agent
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers with default User-Agent if not provided"""
        if headers is None:
            return self.default_headers.copy()
        
        # If headers provided but no User-Agent, add default
        if "User-Agent" not in headers:
            prepared_headers = self.default_headers.copy()
            prepared_headers.update(headers)
            return prepared_headers
        
        # If User-Agent provided, use as-is
        return headers
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, 
                  headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make GET request with retry logic
        
        Args:
            url: The URL to make the request to
            params: Query parameters to include in the URL
            headers: HTTP headers to include in the request
        """
        prepared_headers = self._prepare_headers(headers)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making GET request to {url} (attempt {attempt + 1})")
                
                response = await self.client.get(
                    url, 
                    params=params, 
                    headers=prepared_headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"GET request successful: {url}")
                return result
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e.response.status_code}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.RequestError as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None,
                   json_data: Optional[Dict[str, Any]] = None,
                   params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make POST request with retry logic
        
        Args:
            url: The URL to make the request to
            data: Form data to send in the request body
            json_data: JSON data to send in the request body
            params: Query parameters to include in the URL
            headers: HTTP headers to include in the request
        """
        prepared_headers = self._prepare_headers(headers)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making POST request to {url} (attempt {attempt + 1})")
                
                response = await self.client.post(
                    url,
                    data=data,
                    json=json_data,
                    params=params,
                    headers=prepared_headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"POST request successful: {url}")
                return result
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e.response.status_code}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except httpx.RequestError as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def close(self):
        """Close the async client"""
        await self.client.aclose()
