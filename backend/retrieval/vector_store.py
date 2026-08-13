import os
import faiss
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from backend.utils.config import settings
from backend.utils.logger import logger
from backend.embeddings.embedding_service import EmbeddingService

class VectorStore:
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.base_dir = Path(settings.data_dir) / "indexes" / repo_id
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.index_path = self.base_dir / "index.faiss"
        self.metadata_path = self.base_dir / "chunks.json"
        
        self.embedder = EmbeddingService()
        self.chunks: List[Dict[str, Any]] = []
        
        if self.index_path.exists() and self.metadata_path.exists():
            self.load()
        else:
            # Initialize empty FAISS index (Inner Product for normalized embeddings = Cosine Similarity)
            self.index = faiss.IndexFlatIP(self.embedder.dimension)
            
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Embeds and adds chunks to the FAISS index."""
        if not chunks:
            return
            
        texts = [chunk["content"] for chunk in chunks]
        logger.info(f"Embedding {len(texts)} chunks for {self.repo_id}...")
        embeddings = self.embedder.embed_batch(texts)
        
        # Convert to float32 numpy array for FAISS
        embeddings_np = np.array(embeddings).astype('float32')
        
        self.index.add(embeddings_np)
        self.chunks.extend(chunks)
        
        self.save()
        logger.info(f"Added {len(chunks)} chunks to FAISS index.")
        
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Searches the vector store for the top_k most similar chunks."""
        if self.index.ntotal == 0:
            return []
            
        query_embedding = self.embedder.embed_text(query)
        query_np = np.array([query_embedding]).astype('float32')
        
        # Search FAISS
        distances, indices = self.index.search(query_np, top_k)
        
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx != -1 and idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(distances[0][i])
                results.append(chunk)
                
        return results
        
    def save(self):
        """Persists the FAISS index and chunk metadata."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'w') as f:
            json.dump(self.chunks, f)
            
    def load(self):
        """Loads the FAISS index and chunk metadata."""
        self.index = faiss.read_index(str(self.index_path))
        with open(self.metadata_path, 'r') as f:
            self.chunks = json.load(f)
            
    @classmethod
    def delete_index(cls, repo_id: str):
        """Deletes a repository's index completely."""
        target_dir = Path(settings.data_dir) / "indexes" / repo_id
        import shutil
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
            logger.info(f"Deleted vector index for {repo_id}")
