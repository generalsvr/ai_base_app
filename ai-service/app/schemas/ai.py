import logging
from pydantic import BaseModel, Field, HttpUrl, create_model
from pydantic.generics import GenericModel
from typing import List, Optional, Any, Dict, Union, Literal, TypeVar, Generic
from datetime import datetime
from enum import Enum

# Provider enum
class Provider(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"
    ZYPHRA = "zyphra"
    REPLICATE = "replicate"


# Generic response format for all AI endpoints
T = TypeVar('T')
class AIResponse(GenericModel, Generic[T]):
    """Generic response format for all AI endpoints"""
    data: T
    model: str
    provider: Provider
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None  # response time, tokens, etc.


# Provider-specific parameter models
class OpenAICompletionParams(BaseModel):
    """OpenAI-specific parameters for completions"""
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class GroqCompletionParams(BaseModel):
    """Groq-specific parameters for completions"""
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = None
    seed: Optional[int] = None


class OpenAIImageParams(BaseModel):
    """OpenAI-specific parameters for image generation"""
    n: Optional[int] = None
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None
    quality: Optional[str] = None
    style: Optional[str] = None


class ReplicateImageParams(BaseModel):
    """Replicate-specific parameters for image generation"""
    guidance_scale: Optional[float] = None
    num_inference_steps: Optional[int] = None
    seed: Optional[int] = None
    go_fast: Optional[bool] = None
    lora_scale: Optional[float] = None
    megapixels: Optional[str] = None
    aspect_ratio: Optional[str] = None
    output_format: Optional[str] = None
    output_quality: Optional[int] = None
    prompt_strength: Optional[float] = None
    disable_safety_checker: Optional[bool] = None
    extra_lora_scale: Optional[float] = None
    extra_lora: Optional[str] = None


class ZyphraTTSParams(BaseModel):
    """Zyphra-specific parameters for text-to-speech"""
    speaking_rate: Optional[float] = 15.0
    language_iso_code: Optional[str] = None
    mime_type: Optional[str] = None
    emotion: Optional[Dict[str, float]] = None
    vqscore: Optional[float] = None
    speaker_noised: Optional[bool] = None


# Completion models
class CompletionRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to complete")
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI
    stream: Optional[bool] = False
    user_id: Optional[str] = None
    
    # Provider-specific parameters
    openai_params: Optional[OpenAICompletionParams] = None
    groq_params: Optional[GroqCompletionParams] = None
    
    def get_provider_params(self) -> Dict[str, Any]:
        """Get the parameters for the specified provider"""
        if self.provider == Provider.OPENAI and self.openai_params:
            return self.openai_params.dict(exclude_none=True)
        elif self.provider == Provider.GROQ and self.groq_params:
            return self.groq_params.dict(exclude_none=True)
        return {}


class CompletionChoice(BaseModel):
    text: str
    index: int
    finish_reason: Optional[str] = None


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: datetime
    model: str
    choices: List[CompletionChoice]
    usage: Optional[CompletionUsage] = None


# Embedding models
class EmbeddingRequest(BaseModel):
    input: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI
    user_id: Optional[str] = None


class EmbeddingData(BaseModel):
    embedding: List[float]
    index: int
    object: str


class EmbeddingResponse(BaseModel):
    data: List[EmbeddingData]


class EmbeddingDB(BaseModel):
    id: int
    text: str
    content: str
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime


# Similarity models
class SimilarityRequest(BaseModel):
    query: str
    model: Optional[str] = None
    limit: Optional[int] = 5
    threshold: Optional[float] = 0.7
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI
    user_id: Optional[str] = None


class SimilarityResult(BaseModel):
    text: str
    score: float
    created_at: datetime


class SimilarityResponse(BaseModel):
    results: List[SimilarityResult]


# Image processing models
class ImageProcessingRequest(BaseModel):
    """Request for image processing"""
    prompt: str = Field(..., description="Text prompt for image processing")
    # Either images list, image_url, or image_base64 must be provided
    images: Optional[List[str]] = Field(None, description="List of base64-encoded images or URLs to process")
    image_url: Optional[str] = Field(None, description="URL of the image to process")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image to process")
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI
    user_id: Optional[str] = None


class ImageData(BaseModel):
    """Image data that can be either a URL or base64-encoded content"""
    url: Optional[str] = None
    base64_data: Optional[str] = None
    content_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    

# Define an alias for the generic AIResponse with ImageData
ImageResponse = AIResponse[ImageData]

# For backward compatibility
class LegacyImageResponse(BaseModel):
    text: str
    model: str
    finish_reason: Optional[str] = None


# Audio models - Transcription
class AudioTranscriptionRequest(BaseModel):
    file_content: bytes = Field(..., description="Audio file content")
    model: Optional[str] = None
    prompt: Optional[str] = None
    language: Optional[str] = None
    temperature: Optional[float] = 0.0
    api_key: Optional[str] = None
    provider: Optional[Provider] = Provider.GROQ
    user_id: Optional[str] = None


class AudioTranscriptionResponse(BaseModel):
    text: str


# TTS models
class TTSRequest(BaseModel):
    text: str = Field(..., description="The text to convert to speech")
    model: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[Provider] = Provider.ZYPHRA
    user_id: Optional[str] = None
    
    # Provider-specific parameters
    zyphra_params: Optional[ZyphraTTSParams] = None
    
    def get_provider_params(self) -> Dict[str, Any]:
        """Get the parameters for the specified provider"""
        if self.provider == Provider.ZYPHRA and self.zyphra_params:
            return self.zyphra_params.dict(exclude_none=True)
        return {}


class TTSCloneVoiceRequest(BaseModel):
    text: str = Field(..., description="The text to convert to speech")
    speaker_audio_base64: str = Field(..., description="Base64 encoded audio file for voice cloning")
    model: Optional[str] = None
    speaking_rate: Optional[float] = 15.0
    language_iso_code: Optional[str] = None
    mime_type: Optional[str] = None
    emotion: Optional[Dict[str, float]] = None
    vqscore: Optional[float] = None
    speaker_noised: Optional[bool] = None
    api_key: Optional[str] = None
    provider: Optional[Provider] = Provider.ZYPHRA
    user_id: Optional[str] = None


class TTSEmotionControl(BaseModel):
    happiness: float = 0.6
    neutral: float = 0.6
    sadness: float = 0.05
    disgust: float = 0.05
    fear: float = 0.05
    surprise: float = 0.05
    anger: float = 0.05
    other: float = 0.5


class TTSSupportedFormat(str, Enum):
    WEBM = "audio/webm"
    OGG = "audio/ogg"
    WAV = "audio/wav"
    MP3 = "audio/mp3"
    MPEG = "audio/mpeg"
    MP4 = "audio/mp4"
    AAC = "audio/aac"


class TTSSupportedLanguage(str, Enum):
    ENGLISH_US = "en-us"
    FRENCH = "fr-fr"
    GERMAN = "de"
    JAPANESE = "ja"
    KOREAN = "ko"
    MANDARIN = "cmn"


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    model: Optional[str] = None
    num_outputs: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    api_key: Optional[str] = None
    provider: Optional[Provider] = Provider.REPLICATE
    user_id: Optional[str] = None
    
    # Provider-specific parameters
    replicate_params: Optional[ReplicateImageParams] = None
    openai_params: Optional[OpenAIImageParams] = None
    
    def get_provider_params(self) -> Dict[str, Any]:
        """Get the parameters for the specified provider"""
        if self.provider == Provider.REPLICATE and self.replicate_params:
            return self.replicate_params.dict(exclude_none=True)
        elif self.provider == Provider.OPENAI and self.openai_params:
            return self.openai_params.dict(exclude_none=True)
        return {} 