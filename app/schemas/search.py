from pydantic import BaseModel, Field
from typing import List, Optional

class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    max_results: int = Field(5, ge=1, le=10, description="Number of results to retrieve")
    conversation_id: Optional[str] = None

class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_found: int
