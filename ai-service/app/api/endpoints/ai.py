import logging
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.ai import (
    CompletionRequest, CompletionResponse,
    EmbeddingRequest, EmbeddingResponse, EmbeddingData, EmbeddingDB,
    SimilarityRequest, SimilarityResponse, SimilarityResult
)
from app.services.openai_service import OpenAIService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

router = APIRouter()
qdrant_service = QdrantService()


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Create a text completion"""
    try:
        openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
        completion = openai_service.create_completion(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=request.stop
        )
        return completion
    except Exception as e:
        logger.error(f"Error creating completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating completion: {str(e)}")


@router.post("/embeddings", response_model=EmbeddingDB, status_code=status.HTTP_201_CREATED)
async def create_embedding(request: EmbeddingRequest):
    """Create and store an embedding"""
    try:
        # Create the embedding using OpenAI
        openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
        embedding_vector = openai_service.create_embedding(
            input_text=request.input,
            model=request.model
        )
        
        # Store the embedding in Qdrant
        embedding_data = qdrant_service.create_embedding(
            text=request.input,
            embedding=embedding_vector
        )
        
        return embedding_data
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")


@router.get("/embeddings/{embedding_id}", response_model=EmbeddingDB)
async def get_embedding(embedding_id: int):
    """Get an embedding by ID"""
    embedding = qdrant_service.get_embedding_by_id(embedding_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return embedding


@router.delete("/embeddings/{embedding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_embedding(embedding_id: int):
    """Delete an embedding by ID"""
    result = qdrant_service.delete_embedding(embedding_id)
    if not result:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return None


@router.post("/similarity", response_model=SimilarityResponse)
async def find_similar(request: SimilarityRequest):
    """Find text similar to the given query"""
    try:
        # Create the embedding using OpenAI
        openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
        embedding_vector = openai_service.create_embedding(
            input_text=request.query,
            model=request.model
        )
        
        # Find similar embeddings directly with Qdrant
        similar_items = qdrant_service.find_similar(
            query_embedding=embedding_vector, 
            limit=request.limit, 
            threshold=request.threshold
        )
        
        # Format the response
        results = [
            SimilarityResult(
                text=item["text"],
                score=float(item["similarity"]),
                created_at=item["created_at"]
            )
            for item in similar_items
        ]
        
        return SimilarityResponse(results=results)
    except Exception as e:
        logger.error(f"Error finding similar texts: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding similar texts: {str(e)}") 