import aiohttp
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service to send analytics data to analytics-service"""
    
    def __init__(self, analytics_url: str = "http://analytics-service:8083/api/v1"):
        self.analytics_url = analytics_url
        self.ai_call_endpoint = f"{analytics_url}/ai-call"
    
    async def log_ai_call(self, 
                          user_id: str, 
                          model_used: str, 
                          call_type: str, 
                          tokens: int, 
                          response_time: float,
                          success: bool, 
                          error_message: Optional[str] = None) -> bool:
        """
        Log an AI API call to the analytics service
        
        Args:
            user_id: User who made the API call
            model_used: AI model used (e.g., "gpt-4")
            call_type: Type of API call (e.g., "completion", "embedding")
            tokens: Number of tokens used
            response_time: Response time in seconds
            success: Whether the call was successful
            error_message: Error message if the call failed
            
        Returns:
            bool: Whether the logging was successful
        """
        try:
            # Make sure call_type is not empty
            if not call_type or call_type.strip() == "":
                call_type = "unknown"
                
            payload = {
                "userID": user_id,
                "modelUsed": model_used,
                "callType": call_type,
                "tokens": tokens,
                "responseTime": response_time,
                "success": success
            }
            
            if error_message:
                payload["errorMessage"] = error_message
                
            async with aiohttp.ClientSession() as session:
                async with session.post(self.ai_call_endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to log AI call: {error_text}")
                        return False
                    return True
                    
        except Exception as e:
            logger.error(f"Error logging AI call: {e}")
            return False 