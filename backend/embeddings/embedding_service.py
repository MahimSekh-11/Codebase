import threading
import os
from typing import List
from backend.utils.config import settings
from backend.utils.logger import logger
from google import genai

class EmbeddingService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super(EmbeddingService, cls).__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance
        
    def _initialize(self):
        logger.info(f"Loading Remote Embedding Model: {settings.embedding_model}...")
        
        api_key = settings.llm_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
        if not api_key:
            logger.error("GEMINI API Key not found. Embeddings will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            
        # Gemini text-embedding-004 has an embedding dimension of 768
        self.dimension = 768 
        logger.info(f"Embedding Model initialized. Dimension: {self.dimension}")
        
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        if not self.client:
            raise ValueError("Gemini Client not initialized.")
            
        response = self.client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
        )
        return response.embeddings[0].values
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        if not self.client:
            raise ValueError("Gemini Client not initialized.")
            
        # The Gemini API accepts a list of strings for batch embedding
        response = self.client.models.embed_content(
            model=settings.embedding_model,
            contents=texts,
        )
        return [emb.values for emb in response.embeddings]
