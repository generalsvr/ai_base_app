import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import datetime
import numpy as np

logger = logging.getLogger(__name__)

class QdrantService:
    """Service for interacting with Qdrant vector database"""
    
    def __init__(self):
        """Initialize the Qdrant client"""
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.collection_name = "embeddings"
        self.vector_size = 1536  # OpenAI's embedding dimension
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists, create it if it doesn't"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection '{self.collection_name}'")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def create_embedding(self, text: str, embedding: List[float]) -> Dict[str, Any]:
        """Create a new embedding in Qdrant and return its metadata"""
        try:
            # Generate a timestamp for created_at
            current_time = time.time()
            timestamp = int(current_time * 1000)  # Convert to milliseconds
            
            # Use the timestamp as the ID to ensure uniqueness
            point_id = int(current_time * 1000000)  # Use microseconds for more uniqueness
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": text,
                            "content": text,
                            "created_at": timestamp,
                            "updated_at": timestamp
                        }
                    )
                ]
            )
            
            # Return the created embedding metadata
            return {
                "id": point_id,
                "text": text,
                "content": text,
                "embedding": embedding,
                "created_at": datetime.datetime.fromtimestamp(current_time),
                "updated_at": datetime.datetime.fromtimestamp(current_time)
            }
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            raise
    
    def get_embedding_by_id(self, embedding_id: int) -> Optional[Dict[str, Any]]:
        """Get an embedding by ID"""
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[embedding_id]
            )
            
            if not points:
                return None
                
            point = points[0]
            payload = point.payload
            
            # Convert timestamp to datetime
            created_at = datetime.datetime.fromtimestamp(payload.get("created_at", 0) / 1000)
            updated_at = datetime.datetime.fromtimestamp(payload.get("updated_at", 0) / 1000)
            
            return {
                "id": point.id,
                "text": payload.get("text", ""),
                "content": payload.get("content", ""),
                "embedding": point.vector,
                "created_at": created_at,
                "updated_at": updated_at
            }
        except Exception as e:
            logger.error(f"Error getting embedding by ID: {e}")
            raise
    
    def delete_embedding(self, embedding_id: int) -> bool:
        """Delete an embedding from Qdrant by ID"""
        try:
            # Check if the embedding exists
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[embedding_id]
            )
            
            if not points:
                return False
                
            # Delete from Qdrant
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[embedding_id]
                )
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            raise
    
    def find_similar(self, query_embedding: List[float], limit: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar embeddings using Qdrant search"""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold  # Qdrant uses cosine similarity, not distance
            )
            
            similar_items = []
            for result in results:
                payload = result.payload
                # Convert timestamp to datetime
                created_at = datetime.datetime.fromtimestamp(payload.get("created_at", 0) / 1000)
                
                similar_items.append({
                    "id": result.id,
                    "text": payload.get("text", ""),
                    "content": payload.get("content", ""),
                    "similarity": result.score,
                    "created_at": created_at
                })
            
            return similar_items
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {e}")
            raise 