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
            return False, None
            
        # Skip validation in development mode with special test key
        if os.getenv("APP_ENV") == "development" and api_key == "sk_test_api_key":
            return True, {"id": 1, "username": "test_user", "is_active": True}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.validate_key_endpoint, 
                    json={"api_key": api_key}
                ) as response:
                    if response.status != 200:
                        logger.warning(f"API key validation failed with status {response.status}")
                        return False, None
                        
                    data = await response.json()
                    return True, data.get("user")
                    
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False, None 