from typing import List, Dict, Any
from backend.utils.logger import logger

class Reranker:
    """
    Optional reranking step.
    In a full production environment, this would use a cross-encoder model like BAAI/bge-reranker.
    For this MVP, it acts as a passthrough if reranking is enabled, or simply truncates to top_k.
    """
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        if self.enabled:
            logger.info("Reranker is enabled. (Using stub implementation for MVP).")
            
    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled:
            return chunks[:top_k]
            
        # In a real implementation:
        # scores = cross_encoder.predict([(query, chunk["content"]) for chunk in chunks])
        # Sort chunks by scores
        
        # Stub: just sort by the original vector search score
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_chunks[:top_k]
