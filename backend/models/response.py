from pydantic import BaseModel
from typing import List, Optional

class SourceNode(BaseModel):
    file: str
    symbol: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    score: Optional[float] = None
    content_snippet: Optional[str] = None

class IndexRepositoryResponse(BaseModel):
    repository_id: str
    repository_name: str
    file_count: int
    chunk_count: int
    status: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    retrieval_time: float
    generation_time: float

class RepositoryStats(BaseModel):
    repository_id: str
    repository_name: str
    file_count: int
    chunk_count: int
    languages: dict[str, int]
    size_kb: float
