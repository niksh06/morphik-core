import asyncio
import json
import logging
from typing import List, Optional, Tuple

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.http.models import Distance, VectorParams

from core.models.chunk import DocumentChunk

from .base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class QdrantStore(BaseVectorStore):
    """Qdrant implementation for vector storage."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "morphik_embeddings",
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize Qdrant client for vector storage.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection to store vectors
            api_key: API key for Qdrant Cloud (optional)
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay in seconds between retry attempts
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize Qdrant client
        self.client = AsyncQdrantClient(
            host=host,
            port=port,
            api_key=api_key,
        )
        
        logger.info(f"Initialized Qdrant client for {host}:{port}")

    async def _retry_operation(self, operation, *args, **kwargs):
        """Execute operation with retry logic."""
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                attempt += 1
                if attempt < self.max_retries:
                    logger.warning(
                        f"Qdrant operation attempt {attempt} failed: {str(e)}. "
                        f"Retrying in {self.retry_delay} seconds..."
                    )
                    await asyncio.sleep(self.retry_delay)

        logger.error(f"All Qdrant operation attempts failed after {self.max_retries} retries: {str(last_error)}")
        raise last_error

    async def initialize(self):
        """Initialize Qdrant collection."""
        try:
            # Import config to get vector dimensions
            from core.config import get_settings

            settings = get_settings()
            dimensions = settings.VECTOR_DIMENSIONS

            logger.info(f"Initializing Qdrant collection '{self.collection_name}' with {dimensions} dimensions")

            # Check if collection exists
            try:
                collections = await self._retry_operation(self.client.get_collections)
                collection_exists = any(
                    collection.name == self.collection_name 
                    for collection in collections.collections
                )
            except Exception:
                collection_exists = False

            if collection_exists:
                # Check if dimensions match
                try:
                    collection_info = await self._retry_operation(
                        self.client.get_collection, 
                        self.collection_name
                    )
                    current_dim = collection_info.config.params.vectors.size
                    
                    if current_dim != dimensions:
                        logger.warning(
                            f"Vector dimensions changed from {current_dim} to {dimensions}. "
                            "This requires recreating the collection and will delete all existing vector data."
                        )
                        
                        # Delete existing collection
                        await self._retry_operation(
                            self.client.delete_collection, 
                            self.collection_name
                        )
                        logger.info(f"Deleted existing collection '{self.collection_name}'")
                        collection_exists = False
                    else:
                        logger.info(f"Collection '{self.collection_name}' already exists with correct dimensions")
                        return True
                except Exception as e:
                    logger.warning(f"Could not check collection dimensions: {str(e)}")
                    collection_exists = False

            if not collection_exists:
                # Create new collection
                await self._retry_operation(
                    self.client.create_collection,
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=dimensions,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' with {dimensions} dimensions")

            return True

        except Exception as e:
            logger.error(f"Error initializing Qdrant store: {str(e)}")
            return False

    async def store_embeddings(self, chunks: List[DocumentChunk]) -> Tuple[bool, List[str]]:
        """Store document chunks and their embeddings in Qdrant."""
        if not chunks:
            return True, []

        # Prepare points for Qdrant
        points = []
        stored_ids = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.embedding:
                continue
                
            # Create unique ID for the point
            point_id = f"{chunk.document_id}_{chunk.chunk_number}"
            
            # Prepare payload with metadata
            payload = {
                "document_id": chunk.document_id,
                "chunk_number": chunk.chunk_number,
                "content": chunk.content,
                "metadata": chunk.metadata or {},
            }
            
            # Create point
            point = models.PointStruct(
                id=point_id,
                vector=chunk.embedding,
                payload=payload,
            )
            points.append(point)
            stored_ids.append(point_id)

        if not points:
            logger.warning("No embeddings to store – all chunks had empty vectors")
            return True, []

        try:
            # Store points in Qdrant
            await self._retry_operation(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points,
            )
            
            logger.info(f"Successfully stored {len(points)} embeddings in Qdrant")
            return True, stored_ids

        except Exception as e:
            logger.error(f"Error storing embeddings in Qdrant: {str(e)}")
            return False, []

    async def query_similar(
        self,
        query_embedding: List[float],
        k: int,
        doc_ids: Optional[List[str]] = None,
    ) -> List[DocumentChunk]:
        """Find similar chunks using cosine similarity."""
        try:
            # Prepare search filter if doc_ids are provided
            search_filter = None
            if doc_ids:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchAny(any=doc_ids),
                        )
                    ]
                )

            # Search for similar vectors
            search_result = await self._retry_operation(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False,  # Don't return vectors to save bandwidth
            )

            # Convert results to DocumentChunks
            chunks = []
            for scored_point in search_result:
                payload = scored_point.payload
                
                # Create DocumentChunk with similarity score
                chunk = DocumentChunk(
                    document_id=payload["document_id"],
                    chunk_number=payload["chunk_number"],
                    content=payload["content"],
                    embedding=[],  # Don't send embeddings back
                    metadata=payload.get("metadata", {}),
                    score=scored_point.score,  # Qdrant already returns normalized score [0, 1]
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error(f"Error querying similar chunks from Qdrant: {str(e)}")
            return []

    async def get_chunks_by_id(
        self,
        chunk_identifiers: List[Tuple[str, int]],
    ) -> List[DocumentChunk]:
        """Retrieve specific chunks by document ID and chunk number."""
        try:
            if not chunk_identifiers:
                return []

            # Create point IDs from identifiers
            point_ids = [f"{doc_id}_{chunk_num}" for doc_id, chunk_num in chunk_identifiers]

            # Retrieve points by IDs
            points = await self._retry_operation(
                self.client.retrieve,
                collection_name=self.collection_name,
                ids=point_ids,
                with_payload=True,
                with_vectors=False,
            )

            # Convert to DocumentChunks
            chunks = []
            for point in points:
                if point.payload:
                    chunk = DocumentChunk(
                        document_id=point.payload["document_id"],
                        chunk_number=point.payload["chunk_number"],
                        content=point.payload["content"],
                        embedding=[],  # Don't send embeddings back
                        metadata=point.payload.get("metadata", {}),
                        score=0.0,  # No relevance score for direct retrieval
                    )
                    chunks.append(chunk)

            logger.debug(f"Retrieved {len(chunks)} chunks from Qdrant")
            return chunks

        except Exception as e:
            logger.error(f"Error retrieving chunks by ID from Qdrant: {str(e)}")
            return []

    async def delete_chunks_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks associated with a document."""
        try:
            # Delete points with matching document_id
            delete_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )

            await self._retry_operation(
                self.client.delete,
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(filter=delete_filter),
            )

            logger.info(f"Successfully deleted chunks for document '{document_id}' from Qdrant")
            return True

        except Exception as e:
            logger.error(f"Error deleting chunks for document '{document_id}' from Qdrant: {str(e)}")
            return False

    async def close(self):
        """Close the Qdrant client connection."""
        try:
            await self.client.close()
            logger.info("Closed Qdrant client connection")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {str(e)}")