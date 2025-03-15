import logging
import os
import base64
from typing import Dict, Any, Optional, List, Union, BinaryIO
from zyphra import ZyphraClient

from app.core.config import settings

logger = logging.getLogger(__name__)


class ZyphraService:
    """Service for interacting with Zyphra TTS API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Zyphra client with API key"""
        self.api_key = api_key or settings.ZYPHRA_API_KEY
        
        if not self.api_key:
            logger.warning("Zyphra API key not provided. API calls will fail.")
        
        self.client = ZyphraClient(api_key=self.api_key)
    
    async def generate_speech(
        self,
        text: str,
        model: Optional[str] = None,
        speaking_rate: Optional[float] = 15.0,
        language_iso_code: Optional[str] = None,
        mime_type: Optional[str] = None,
        emotion: Optional[Dict[str, float]] = None,
        vqscore: Optional[float] = None,
        speaker_noised: Optional[bool] = None,
        speaker_audio: Optional[str] = None
    ) -> bytes:
        """
        Generate speech from text using Zyphra TTS API.
        
        Args:
            text: The text to convert to speech
            model: TTS model selection (zonos-v0.1-transformer or zonos-v0.1-hybrid)
            speaking_rate: Speed of speech (5 to 35)
            language_iso_code: Language code (e.g., "en-us", "fr-fr")
            mime_type: Output audio format (e.g., "audio/webm")
            emotion: Emotional weights for speech generation
            vqscore: Voice quality score (hybrid model only, 0.6 to 0.8)
            speaker_noised: Denoises to improve voice stability (hybrid model only)
            speaker_audio: Base64-encoded audio file for voice cloning
            
        Returns:
            Binary audio data
        """
        try:
            model = model or settings.DEFAULT_ZYPHRA_MODEL
            
            # Build request parameters
            params = {
                "text": text,
                "speaking_rate": speaking_rate,
                "model": model
            }
            
            # Add optional parameters if provided
            if language_iso_code:
                params["language_iso_code"] = language_iso_code
            
            if mime_type:
                params["mime_type"] = mime_type
                
            if emotion:
                # Convert dictionary to EmotionWeights object if needed
                params["emotion"] = emotion
                
            if vqscore is not None and model == "zonos-v0.1-hybrid":
                params["vqscore"] = max(0.6, min(0.8, vqscore))  # Ensure value is within range
                
            if speaker_noised is not None and model == "zonos-v0.1-hybrid":
                params["speaker_noised"] = speaker_noised
                
            if speaker_audio:
                params["speaker_audio"] = speaker_audio
            
            # Generate speech
            audio_data = self.client.audio.speech.create(**params)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating speech with Zyphra: {e}")
            raise
    
    def process_audio_file(self, file_path: str) -> str:
        """
        Process an audio file and convert it to base64 for voice cloning.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Base64-encoded audio data
        """
        try:
            with open(file_path, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return audio_base64
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            raise
            
    def process_audio_bytes(self, audio_bytes: bytes) -> str:
        """
        Process audio bytes and convert to base64 for voice cloning.
        
        Args:
            audio_bytes: Raw audio bytes
            
        Returns:
            Base64-encoded audio data
        """
        try:
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return audio_base64
            
        except Exception as e:
            logger.error(f"Error processing audio bytes: {e}")
            raise 