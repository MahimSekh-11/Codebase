import threading
from sentence_transformers import SentenceTransformer
from typing import List
from backend.utils.config import settings
from backend.utils.logger import logger

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
        logger.info(f"Loading Embedding Model: {settings.embedding_model}...")
        self.model = SentenceTransformer(settings.embedding_model)
        # BAAI/bge-small-en-v1.5 has an embedding dimension of 384
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding Model loaded. Dimension: {self.dimension}")
        
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        # For bge models, queries should sometimes have a prefix, but for codebase RAG, 
        # standard embedding often works fine, or we can just rely on the model defaults.
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()
