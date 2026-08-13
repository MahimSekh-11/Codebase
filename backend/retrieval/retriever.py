import time
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.reranker import Reranker
from backend.llm.provider import LLMProvider
from backend.llm.prompts import RAG_SYSTEM_PROMPT
from backend.models.response import ChatResponse, SourceNode
from backend.utils.config import settings
from backend.utils.logger import logger

class Retriever:
    def __init__(self):
        self.llm = LLMProvider()
        self.reranker = Reranker(enabled=settings.enable_reranker)
        
    def answer_question(self, repo_id: str, question: str, api_key: str = None) -> ChatResponse:
        t0 = time.time()
        
        # 1. Retrieve
        logger.info(f"Retrieving chunks for '{question}' from repo '{repo_id}'")
        vector_store = VectorStore(repo_id)
        # Fetch more initially if reranking, else just fetch top_k
        fetch_k = settings.top_k * 2 if settings.enable_reranker else settings.top_k
        retrieved_chunks = vector_store.search(question, top_k=fetch_k)
        
        # 2. Rerank
        final_chunks = self.reranker.rerank(question, retrieved_chunks, top_k=settings.top_k)
        retrieval_time = time.time() - t0
        
        # 3. Construct Context
        context_parts = []
        sources = []
        for i, chunk in enumerate(final_chunks):
            # Prepare prompt context
            file_path = chunk.get("file_path", "unknown")
            start = chunk.get("start_line", "?")
            end = chunk.get("end_line", "?")
            symbol = chunk.get("symbol_name", "unknown")
            content = chunk.get("content", "")
            
            context_parts.append(
                f"--- Source {i+1} ---\n"
                f"File: {file_path}\n"
                f"Symbol: {symbol}\n"
                f"Lines: {start}-{end}\n"
                f"Code:\n{content}\n"
            )
            
            # Prepare source nodes for response
            sources.append(SourceNode(
                file=file_path,
                symbol=symbol,
                start_line=start if isinstance(start, int) else None,
                end_line=end if isinstance(end, int) else None,
                score=chunk.get("score"),
                content_snippet=content[:200] + "..." if len(content) > 200 else content
            ))
            
        context_str = "\n".join(context_parts)
        
        # 4. Generate
        t1 = time.time()
        prompt = RAG_SYSTEM_PROMPT.format(context=context_str, question=question)
        answer = self.llm.generate(prompt, api_key=api_key)
        generation_time = time.time() - t1
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            retrieval_time=retrieval_time,
            generation_time=generation_time
        )
