import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Qdrant settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # OpenAI API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Application settings
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    DEFAULT_COMPLETION_MODEL: str = "gpt-3.5-turbo-instruct"
    
    # API settings
    API_PREFIX: str = "/api/v1"


settings = Settings() 