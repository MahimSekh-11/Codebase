from pydantic import BaseModel, HttpUrl
from typing import Optional

class IndexRepositoryRequest(BaseModel):
    repo_url: HttpUrl

class ChatRequest(BaseModel):
    repository_id: str
    question: str
    history_window: Optional[int] = 5
