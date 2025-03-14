from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

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


class SimilarityResult(BaseModel):
    text: str
    score: float
    created_at: datetime


class SimilarityResponse(BaseModel):
    results: List[SimilarityResult] 