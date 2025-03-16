from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional, Dict
import logging
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Define the API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize auth service
auth_service = AuthService()

async def get_current_user(api_key: str = Depends(api_key_header)) -> Dict:
    """
    Dependency to validate the API key and get the current user
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        The user data if API key is valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    logger.debug(f"Validating API key: {api_key[:10]}... (length: {len(api_key) if api_key else 0})")
    
    if not api_key:
        logger.warning("API key is missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Validate the API key
    logger.debug(f"Sending API key to validation endpoint: {auth_service.validate_key_endpoint}")
    is_valid, user_data = await auth_service.validate_api_key(api_key)
    
    if not is_valid or not user_data:
        logger.warning(f"Invalid API key: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    logger.debug(f"API key validation successful for user: {user_data.get('username')}")
    
    # Ensure user is active
    if not user_data.get("is_active", False):
        logger.warning(f"User account is inactive: {user_data.get('username')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user_data 