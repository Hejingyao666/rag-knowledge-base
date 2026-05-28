from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_msg: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    doc_ids: Optional[List[str]] = None


class SourceItem(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    model: str


class StatsResponse(BaseModel):
    document_count: int
    total_chunks: int
    collection_name: str