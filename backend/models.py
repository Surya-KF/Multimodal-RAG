from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

class SourceMetadata(BaseModel):
    title: str
    filename: str
    file_type: str
    chunk_index: int
    document_id: str

class SourceInfo(BaseModel):
    content: str
    metadata: SourceMetadata
    relevance_score: float

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceInfo]
    confidence_score: float

class UploadResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    file_type: str
    processed_content_length: int

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_type: str
    upload_time: str
    content_length: int
