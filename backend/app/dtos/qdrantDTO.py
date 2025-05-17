from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SearchQueryRequest(BaseModel):
    query_text: str
    project_id: Optional[int] = None # To filter search by project
    limit: int = Field(default=5, gt=0, le=100)

class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: int
    project_id: int
    file_name: str
    score: float
    text: str # The content of the chunk
    metadata: Dict[str, Any] # Other metadata from the chunk

class SearchResponse(BaseModel):
    results: List[SearchResultItem]