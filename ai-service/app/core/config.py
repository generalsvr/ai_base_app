import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Qdrant settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # OpenAI API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Groq API settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Zyphra API settings
    ZYPHRA_API_KEY: str = os.getenv("ZYPHRA_API_KEY", "")
    
    # Application settings
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    DEFAULT_COMPLETION_MODEL: str = "gpt-3.5-turbo-instruct"
    DEFAULT_VISION_MODEL: str = "gpt-4o-mini"
    
    # Groq specific models
    DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_GROQ_EMBEDDING_MODEL: str = "text-embedding-ada-002"  # Fallback to OpenAI
    DEFAULT_GROQ_TRANSCRIPTION_MODEL: str = "whisper-large-v3-turbo"
    
    # Zyphra specific models
    DEFAULT_ZYPHRA_MODEL: str = "zonos-v0.1-transformer"
    DEFAULT_ZYPHRA_MIME_TYPE: str = "audio/webm"  # Default audio format
    
    # API settings
    API_PREFIX: str = "/api/v1"


settings = Settings() 