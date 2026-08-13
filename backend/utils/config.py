import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Settings
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str = ""

    # Embedding Settings
    embedding_model: str = "BAAI/bge-small-en-v1.5"

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

    @property
    def resolved_api_key(self) -> str:
        """
        Tries to resolve the API key from multiple possible env var names.
        Works with:
          - LLM_API_KEY (our default, set in .env or Streamlit secrets)
          - GEMINI_API_KEY (common alias)
          - GOOGLE_API_KEY (another common alias)
        """
        return (
            self.llm_api_key
            or os.environ.get("LLM_API_KEY", "")
            or os.environ.get("GEMINI_API_KEY", "")
            or os.environ.get("GOOGLE_API_KEY", "")
        )


settings = Settings()
