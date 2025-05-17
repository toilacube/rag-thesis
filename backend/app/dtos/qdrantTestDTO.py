from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TestPointData(BaseModel):
    id: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict) # e.g., {"source": "manual_test", "page": 1}

class TestUpsertRequest(BaseModel):
    points: List[TestPointData]
    project_id_for_points: Optional[int] = 1 # Default project_id for test points payload
    document_id_for_points: Optional[int] = 1 # Default document_id for test points payload

class CollectionInfoResponse(BaseModel):
    status: str
    optimizer_status: str
    vectors_count: int
    indexed_vectors_count: Optional[int] = None
    points_count: int
    segments_count: int
    config: dict
    payload_schema: dict