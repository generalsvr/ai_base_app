import logging
import openai
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the OpenAI client with API key and base URL"""
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided. API calls will fail.")
        
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def create_completion(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        max_tokens: int = 150,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a text completion using OpenAI API"""
        try:
            model = model or settings.DEFAULT_COMPLETION_MODEL
            
            completion = self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop
            )
            
            return {
                "id": completion.id,
                "choices": [{
                    "text": choice.text,
                    "index": choice.index,
                    "logprobs": choice.logprobs,
                    "finish_reason": choice.finish_reason
                } for choice in completion.choices],
                "created": completion.created,
                "model": completion.model
            }
            
        except Exception as e:
            logger.error(f"Error creating completion: {e}")
            raise
    
    def create_embedding(
        self, 
        input_text: str, 
        model: Optional[str] = None
    ) -> List[float]:
        """Create an embedding for the given text using OpenAI API"""
        try:
            model = model or settings.DEFAULT_EMBEDDING_MODEL
            
            response = self.client.embeddings.create(
                model=model,
                input=input_text
            )
            
            if not response.data:
                raise ValueError("No embedding data returned from OpenAI API")
                
            # Return the embedding vector
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            raise 