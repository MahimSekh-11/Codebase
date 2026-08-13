import threading
from typing import List
from backend.utils.config import settings
from backend.utils.logger import logger


class EmbeddingService:
    """
    Thread-safe singleton embedding service using fastembed (ONNX-based).
    fastembed uses ~150MB RAM vs sentence-transformers+torch which uses ~600MB.
    Same model and output dimensions (384) as BAAI/bge-small-en-v1.5.
    """
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
        from fastembed import TextEmbedding
        model_name = settings.embedding_model or "BAAI/bge-small-en-v1.5"
        logger.info(f"Loading Embedding Model (fastembed/ONNX): {model_name}...")
        self.model = TextEmbedding(model_name=model_name)
        # Get dimension by running a test embed
        test = list(self.model.embed(["test"]))
        self.dimension = len(test[0])
        logger.info(f"Embedding Model loaded. Dimension: {self.dimension}")

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        results = list(self.model.embed([text]))
        return results[0].tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings efficiently."""
        results = list(self.model.embed(texts))
        return [r.tolist() for r in results]
