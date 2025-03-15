from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Any, Dict, Union, Literal
from datetime import datetime
from enum import Enum

# Provider enum
class Provider(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"
    ZYPHRA = "zyphra"

# Completion models
class CompletionRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    stop: Optional[List[str]] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI


class Choice(BaseModel):
    text: str
    index: int
    logprobs: Optional[Any] = None
    finish_reason: str


class CompletionResponse(BaseModel):
    id: str
    choices: List[Choice]
    created: int
    model: str


# Embedding models
class EmbeddingRequest(BaseModel):
    input: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI


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


class SimilarityResult(BaseModel):
    text: str
    score: float
    created_at: datetime


class SimilarityResponse(BaseModel):
    results: List[SimilarityResult]


# Image processing models
class ImageUrlRequest(BaseModel):
    prompt: str
    image_url: HttpUrl
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI


class ImageFileRequest(BaseModel):
    prompt: str
    image_base64: str = Field(..., description="Base64 encoded image data")
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: Optional[Provider] = Provider.OPENAI


class ImageResponse(BaseModel):
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


class AudioTranscriptionResponse(BaseModel):
    text: str


# TTS models
class TTSRequest(BaseModel):
    text: str = Field(..., description="The text to convert to speech")
    model: Optional[str] = None
    speaking_rate: Optional[float] = 15.0
    language_iso_code: Optional[str] = None
    mime_type: Optional[str] = None
    emotion: Optional[Dict[str, float]] = None
    vqscore: Optional[float] = None
    speaker_noised: Optional[bool] = None
    api_key: Optional[str] = None
    provider: Optional[Provider] = Provider.ZYPHRA


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