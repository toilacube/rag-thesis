import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from fastapi import Depends

from app.config.config import Config, getConfig

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, settings: Config = Depends(getConfig)):
        self.settings = settings
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
                # prefer_grpc=True, # Generally recommended for performance
            )
            logger.info(f"Successfully connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            # Depending on the application's needs, you might want to raise this exception
            # or handle it in a way that the app can still run in a degraded mode.
            self.client = None # Or raise

        try:
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info(f"Successfully loaded embedding model: {settings.EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {settings.EMBEDDING_MODEL_NAME}: {e}")
            self.embedding_model = None # Or raise

        if self.client and self.embedding_model:
            self.ensure_collection()

    def ensure_collection(self):
        if not self.client:
            logger.error("Qdrant client not initialized. Cannot ensure collection.")
            return
        try:
            collection_name = self.settings.QDRANT_COLLECTION_NAME
            # Check if collection exists
            try:
                self.client.get_collection(collection_name=collection_name)
                logger.info(f"Collection '{collection_name}' already exists.")
            except Exception:  # More specific exception for "not found" might be available
                logger.info(f"Collection '{collection_name}' not found. Creating it.")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.settings.EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info(f"Collection '{collection_name}' created successfully.")
                # Create payload indexes for faster filtering if needed
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="project_id",
                    field_schema=models.PayloadSchemaType.INTEGER
                )
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_id",
                    field_schema=models.PayloadSchemaType.INTEGER
                )
                logger.info(f"Payload indexes for 'project_id' and 'document_id' created on '{collection_name}'.")

        except Exception as e:
            logger.error(f"Error during Qdrant collection setup for '{self.settings.QDRANT_COLLECTION_NAME}': {e}")
            # Potentially raise or handle to prevent app startup if Qdrant is critical

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.embedding_model:
            logger.error("Embedding model not loaded.")
            raise RuntimeError("Embedding model not available")
        
        logger.info(f"Generating embeddings for {len(texts)} texts.")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        logger.info(f"Embeddings generated successfully.")
        return embeddings.tolist()

    def upsert_chunks(self, points: List[models.PointStruct]):
        if not self.client:
            logger.error("Qdrant client not initialized. Cannot upsert points.")
            raise RuntimeError("Qdrant client not available")

        collection_name = self.settings.QDRANT_COLLECTION_NAME
        if not points:
            logger.info("No points to upsert.")
            return

        logger.info(f"Upserting {len(points)} points to collection '{collection_name}'.")
        try:
            # Consider batching if len(points) is very large
            self.client.upsert(collection_name=collection_name, points=points, wait=True)
            logger.info(f"Successfully upserted {len(points)} points.")
        except Exception as e:
            logger.error(f"Error upserting points to Qdrant collection '{collection_name}': {e}")
            raise

    def search_chunks(
        self,
        query_text: str,
        project_id: Optional[int] = None,
        limit: int = 5
    ) -> List[models.ScoredPoint]:
        if not self.client or not self.embedding_model:
            logger.error("Qdrant client or embedding model not initialized. Cannot perform search.")
            raise RuntimeError("Qdrant client or embedding model not available")

        collection_name = self.settings.QDRANT_COLLECTION_NAME
        logger.info(f"Searching in collection '{collection_name}' for query: '{query_text}' with limit {limit}.")
        
        query_embedding = self.get_embeddings([query_text])[0]

        search_filter = None
        if project_id is not None:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=project_id),
                    )
                ]
            )
            logger.info(f"Applying filter for project_id: {project_id}")

        try:
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                with_payload=True # Ensure payload is returned
            )
            logger.info(f"Found {len(search_results)} results.")
            return search_results
        except Exception as e:
            logger.error(f"Error searching in Qdrant collection '{collection_name}': {e}")
            raise

# Dependency for FastAPI
def get_qdrant_service(settings: Config = Depends(getConfig)) -> QdrantService:
    # This could be a singleton if model loading is very heavy,
    # but for now, a new instance per request (with shared model potentially cached by SentenceTransformer) is fine.
    # For true singleton, manage instance at app level.
    return QdrantService(settings)