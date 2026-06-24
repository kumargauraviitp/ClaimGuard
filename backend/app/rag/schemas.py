from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class CitationSchema(BaseModel):
    chunk_id: str
    document_id: str
    source_title: str
    source_type: str
    version: str
    relevance_score: float
    content: str

class SearchResponse(BaseModel):
    context_text: str
    citations: List[CitationSchema]
