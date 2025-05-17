import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.dtos.qdrantDTO import SearchQueryRequest, SearchResponse, SearchResultItem
from app.dtos.qdrantTestDTO import TestUpsertRequest, TestPointData, CollectionInfoResponse
from app.config.config import getConfig # To get collection name

# If you have user authentication, you might want to protect these test endpoints
# from app.core.security import get_current_user 
# from app.models.models import User

from qdrant_client import models as qdrant_models

logger = logging.getLogger(__name__)
router = APIRouter(
    # prefix="/qdrant-test", # Prefix for all routes in this router
    # tags=["Qdrant Test"],    # Tag for OpenAPI documentation
)

config = getConfig() # Load config to get collection name

@router.post(
    "/upsert-points",
    summary="Manually upsert test points to Qdrant",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any] # Simple response
)
async def test_upsert_points(
    request_data: TestUpsertRequest,
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    # current_user: User = Depends(get_current_user) # Optional: for protected endpoints
):
    """
    Manually creates embeddings for given texts and upserts them into Qdrant.
    This is for testing the embedding and upsertion process.
    """
    if not qdrant_service.client or not qdrant_service.embedding_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant client or embedding model is not available."
        )

    if not request_data.points:
        return {"message": "No points provided to upsert."}

    points_to_upsert: List[qdrant_models.PointStruct] = []
    texts_for_embedding: List[str] = [p.text for p in request_data.points]

    try:
        embeddings = qdrant_service.get_embeddings(texts_for_embedding)
    except Exception as e:
        logger.error(f"Error generating embeddings for test points: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {e}"
        )

    for i, point_data in enumerate(request_data.points):
        payload = point_data.metadata.copy() # Start with provided metadata
        # Add common fields similar to your main pipeline for consistency in search tests
        payload.update({
            "text": point_data.text,
            "document_id": request_data.document_id_for_points,
            "project_id": request_data.project_id_for_points,
            "file_name": payload.get("file_name", "manual_test_file.txt"),
            "db_chunk_id": point_data.id, # Using the provided ID as the db_chunk_id for payload
            "chunk_metadata": point_data.metadata # Storing original metadata under chunk_metadata
        })

        points_to_upsert.append(
            qdrant_models.PointStruct(
                id=point_data.id, # Use the provided ID as Qdrant point ID
                vector=embeddings[i],
                payload=payload
            )
        )
    
    try:
        qdrant_service.upsert_chunks(points=points_to_upsert)
        return {
            "message": f"Successfully upserted {len(points_to_upsert)} test points.",
            "point_ids": [p.id for p in request_data.points]
        }
    except Exception as e:
        logger.error(f"Error upserting test points to Qdrant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upsert points to Qdrant: {e}"
        )

@router.post(
    "/search-points",
    summary="Manually search points in Qdrant",
    response_model=SearchResponse 
)
async def test_search_points(
    search_request: SearchQueryRequest, # Reuse existing DTO
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    # current_user: User = Depends(get_current_user) # Optional
):
    """
    Searches Qdrant using the provided query text.
    Allows specifying a project_id for filtering and a limit for results.
    """
    if not qdrant_service.client or not qdrant_service.embedding_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant client or embedding model is not available."
        )
    try:
        search_hits = qdrant_service.search_chunks(
            query_text=search_request.query_text,
            project_id=search_request.project_id,
            limit=search_request.limit
        )
        
        results = []
        for hit in search_hits:
            payload = hit.payload if hit.payload else {}
            results.append(SearchResultItem(
                chunk_id=str(hit.id), # Qdrant ID can be int or UUID string or your custom string
                document_id=payload.get("document_id"),
                project_id=payload.get("project_id"),
                file_name=payload.get("file_name", "N/A"),
                score=hit.score,
                text=payload.get("text", ""), # Text from the payload
                metadata=payload.get("chunk_metadata", {}) # Metadata from the payload
            ))
        return SearchResponse(results=results)

    except RuntimeError as e:
        logger.error(f"Runtime error during Qdrant search test: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Search service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Qdrant search test: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get(
    "/collection-info",
    summary="Get information about the Qdrant collection",
    response_model=CollectionInfoResponse
)
async def test_get_collection_info(
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    # current_user: User = Depends(get_current_user) # Optional
):
    """
    Retrieves and returns information about the configured Qdrant collection.
    """
    if not qdrant_service.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant client is not available."
        )
    
    collection_name = config.QDRANT_COLLECTION_NAME
    try:
        collection_info = qdrant_service.client.get_collection(collection_name=collection_name)
        
        # Map qdrant_client.models.CollectionInfo to CollectionInfoResponse DTO
        return CollectionInfoResponse(
            status=str(collection_info.status), # Enums to string
            optimizer_status=str(collection_info.optimizer_status), # Enums to string
            vectors_count=collection_info.vectors_count or 0,
            indexed_vectors_count=collection_info.indexed_vectors_count, # Can be None
            points_count=collection_info.points_count or 0,
            segments_count=collection_info.segments_count or 0,
            config=collection_info.config.model_dump(), # Convert Pydantic model to dict
            payload_schema={k: str(v.data_type) for k, v in collection_info.payload_schema.items()} if collection_info.payload_schema else {}
        )
    except Exception as e:
        # Qdrant client might raise specific exceptions for "collection not found"
        logger.error(f"Error getting Qdrant collection info for '{collection_name}': {e}", exc_info=True)
        if "404" in str(e) or "not found" in str(e).lower(): # Basic check
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection '{collection_name}' not found.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection info: {e}"
        )