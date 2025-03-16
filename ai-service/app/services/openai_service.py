import logging
import os
import base64
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator, Union

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
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def create_completion(
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
            
            completion = await self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop
            )
            
            # Log raw response format for debugging
            logger.debug(f"OpenAI API raw completion response: {completion}")
            
            response = {
                "id": completion.id,
                "object": "text_completion",
                "choices": [{
                    "text": choice.text,
                    "index": choice.index,
                    "logprobs": choice.logprobs,
                    "finish_reason": choice.finish_reason
                } for choice in completion.choices],
                "created": completion.created,
                "model": completion.model,
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if hasattr(completion, 'usage') and completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if hasattr(completion, 'usage') and completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if hasattr(completion, 'usage') and completion.usage else 0
                }
            }
            
            # Log transformed response
            logger.debug(f"Transformed completion response: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating completion: {e}")
            raise
    
    async def create_completion_stream(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        max_tokens: int = 150,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a streaming text completion using OpenAI API"""
        try:
            model = model or settings.DEFAULT_COMPLETION_MODEL
            
            stream = await self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                stream=True
            )
            
            # Log first chunk for debugging
            first_chunk = True
            
            async for chunk in stream:
                if first_chunk:
                    logger.debug(f"OpenAI API raw stream chunk: {chunk}")
                
                response = {
                    "id": chunk.id,
                    "object": "text_completion",
                    "choices": [{
                        "text": choice.text,
                        "index": choice.index,
                        "logprobs": choice.logprobs,
                        "finish_reason": choice.finish_reason
                    } for choice in chunk.choices],
                    "created": chunk.created,
                    "model": chunk.model,
                    "usage": {
                        "prompt_tokens": 0,  # Not available in stream chunks
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                
                if first_chunk:
                    logger.debug(f"Transformed stream chunk: {response}")
                    first_chunk = False
                
                yield response
            
        except Exception as e:
            logger.error(f"Error creating streaming completion: {e}")
            raise
    
    async def create_embedding(
        self, 
        input_text: str, 
        model: Optional[str] = None
    ) -> List[float]:
        """Create an embedding for the given text using OpenAI API"""
        try:
            model = model or settings.DEFAULT_EMBEDDING_MODEL
            
            response = await self.client.embeddings.create(
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
    
    async def process_image(
        self,
        prompt: str,
        image_data: Union[str, bytes],
        is_url: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an image with a prompt using OpenAI's multimodal models
        
        Args:
            prompt: Text prompt to accompany the image
            image_data: Either an image URL or the raw image bytes
            is_url: True if image_data is a URL, False if it's raw bytes
            model: Model to use, defaults to settings.DEFAULT_VISION_MODEL
        """
        try:
            model = model or settings.DEFAULT_VISION_MODEL
            
            # Prepare the image content
            if is_url:
                image_url = image_data
            else:
                # Convert bytes to base64 if needed
                if isinstance(image_data, bytes):
                    b64_image = base64.b64encode(image_data).decode("utf-8")
                else:
                    b64_image = image_data
                
                image_url = f"data:image/jpeg;base64,{b64_image}"
            
            # Create the API request using the correct format for vision API
            response = await self.client.responses.create(
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": image_url},
                        ]
                    }
                ]
            )
            
            # Log raw response for debugging
            logger.debug(f"OpenAI Vision API raw response: {response}")
            
            # Extract output text from the response
            result = {
                "data": {
                    "text": response.output_text if hasattr(response, 'output_text') else "",
                },
                "model": model,
                "provider": "openai",
                "finish_reason": None,  # Not provided in this API
                "usage": {
                    "prompt_tokens": 0,  # Not available in this API
                    "completion_tokens": 0,  # Not available in this API
                    "total_tokens": 0  # Not available in this API
                }
            }
            
            logger.info(f"Successfully processed image with model {model}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            # Try to log more details about the error
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def process_image_from_url(
        self,
        prompt: str,
        image_url: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process an image from a URL with a text prompt"""
        return await self.process_image(prompt, image_url, is_url=True, model=model)
    
    async def process_image_from_bytes(
        self,
        prompt: str,
        image_bytes: bytes,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process an image from bytes with a text prompt"""
        return await self.process_image(prompt, image_bytes, is_url=False, model=model) 