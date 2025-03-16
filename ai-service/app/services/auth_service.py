import aiohttp
import logging
from typing import Optional, Dict, Tuple
import os

logger = logging.getLogger(__name__)

class AuthService:
    """Service to authenticate and authorize API requests using API keys"""
    
    def __init__(self, auth_url: str = "http://user-service:8081/api/auth"):
        self.auth_url = auth_url
        self.validate_key_endpoint = f"{auth_url}/validate-key"
    
    async def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate an API key and return user information if valid
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Tuple containing:
              - Boolean indicating if the key is valid
              - User data dictionary (or None if invalid)
        """
        if not api_key or api_key.strip() == "":
            logger.warning("Empty API key provided")
            return False, None
            
        # Skip validation in development mode with special test key
        if os.getenv("APP_ENV") == "development" and api_key == "sk_test_api_key":
            logger.debug("Using development test key")
            return True, {"id": 1, "username": "test_user", "is_active": True}
        
        try:
            logger.debug(f"Validating API key {api_key[:10]}... with user service at {self.validate_key_endpoint}")
            async with aiohttp.ClientSession() as session:
                # Log the request payload for debugging
                payload = {"api_key": api_key}
                logger.debug(f"Request payload: {payload}")
                
                async with session.post(
                    self.validate_key_endpoint, 
                    json=payload
                ) as response:
                    status_code = response.status
                    logger.debug(f"Validation response status: {status_code}")
                    
                    if status_code != 200:
                        logger.warning(f"API key validation failed with status {status_code}")
                        response_text = await response.text()
                        logger.debug(f"Response text: {response_text}")
                        return False, None
                        
                    data = await response.json()
                    logger.debug(f"Validation response data: {data}")
                    return True, data.get("user")
                    
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False, None 