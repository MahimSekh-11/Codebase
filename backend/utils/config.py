import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LLM Settings
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str = ""
    
    # Embedding Settings
    embedding_model: str = "text-embedding-004"
    
    # Retrieval Settings
    top_k: int = 10
    enable_reranker: bool = False
    
    # App limits
    max_repository_size_mb: int = 50
    max_upload_size_mb: int = 50
    
    # Storage
    data_dir: str = "./data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
