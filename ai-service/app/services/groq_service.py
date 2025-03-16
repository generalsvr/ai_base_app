import logging
import os
from groq import Groq, AsyncGroq
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator, Union

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Groq client with API key"""
        self.api_key = api_key or settings.GROQ_API_KEY
        
        if not self.api_key:
            logger.warning("Groq API key not provided. API calls will fail.")
        
        self.client = AsyncGroq(
            api_key=self.api_key
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
        """Create a text completion using Groq API"""
        try:
            model = model or settings.DEFAULT_GROQ_MODEL
            
            # Groq uses chat completions API for all interactions
            chat_completion = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop
            )
            
            # Log raw response format for debugging
            logger.debug(f"Groq API raw completion response: {chat_completion}")
            
            # Map the chat completion response to be compatible with the OpenAI completions API
            completion_text = chat_completion.choices[0].message.content
            
            response = {
                "id": chat_completion.id,
                "object": "text_completion",
                "choices": [{
                    "text": completion_text,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": chat_completion.choices[0].finish_reason
                }],
                "created": chat_completion.created,
                "model": chat_completion.model,
                "usage": {
                    "prompt_tokens": chat_completion.usage.prompt_tokens if hasattr(chat_completion, 'usage') and chat_completion.usage else 0,
                    "completion_tokens": chat_completion.usage.completion_tokens if hasattr(chat_completion, 'usage') and chat_completion.usage else 0,
                    "total_tokens": chat_completion.usage.total_tokens if hasattr(chat_completion, 'usage') and chat_completion.usage else 0
                }
            }
            
            # Log transformed response
            logger.debug(f"Transformed Groq completion response: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating completion with Groq: {e}")
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
        """Create a streaming text completion using Groq API"""
        try:
            model = model or settings.DEFAULT_GROQ_MODEL
            
            # Groq uses chat completions API for all interactions
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                stream=True
            )
            
            # Log first chunk for debugging
            first_chunk = True
            
            async for chunk in stream:
                # Reformat to match the format expected by our API
                if chunk.choices and chunk.choices[0].delta.content:
                    if first_chunk:
                        logger.debug(f"Groq API raw stream chunk: {chunk}")
                    
                    response = {
                        "id": chunk.id,
                        "object": "text_completion",
                        "choices": [{
                            "text": chunk.choices[0].delta.content,
                            "index": 0,
                            "logprobs": None,
                            "finish_reason": chunk.choices[0].finish_reason
                        }],
                        "created": chunk.created,
                        "model": chunk.model,
                        "usage": {
                            "prompt_tokens": 0,  # Not available in stream chunks
                            "completion_tokens": 0,
                            "total_tokens": 0
                        }
                    }
                    
                    if first_chunk:
                        logger.debug(f"Transformed Groq stream chunk: {response}")
                        first_chunk = False
                    
                    yield response
                    
        except Exception as e:
            logger.error(f"Error creating streaming completion with Groq: {e}")
            raise
    
    async def create_embedding(
        self,
        input_text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Create an embedding using Groq API
        Note: As of this implementation, Groq may not support embeddings directly.
        This method is included for API compatibility but may raise an exception.
        """
        try:
            model = model or settings.DEFAULT_GROQ_EMBEDDING_MODEL
            
            logger.warning("Groq may not support direct embedding generation. Falling back to OpenAI if available.")
            raise NotImplementedError("Embedding generation not currently supported by Groq")
            
        except Exception as e:
            logger.error(f"Error creating embedding with Groq: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_file: bytes,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        language: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Groq's Whisper implementation
        """
        try:
            model = model or settings.DEFAULT_GROQ_TRANSCRIPTION_MODEL
            
            # The synchronous client is used here since Groq doesn't specify an async API for audio
            sync_client = Groq(api_key=self.api_key)
            
            # Create a temporary filename
            temp_filename = "audio_file.mp3"
            
            # Create a transcription using the Whisper model
            transcription = sync_client.audio.transcriptions.create(
                file=(temp_filename, audio_file),  # Pass a tuple of (filename, content)
                model=model,
                prompt=prompt,
                language=language,
                temperature=temperature,
                response_format="json"
            )
            
            return {
                "text": transcription.text
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio with Groq: {e}")
            raise 