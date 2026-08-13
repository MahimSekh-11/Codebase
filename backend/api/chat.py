from fastapi import APIRouter, HTTPException
from backend.models.request import ChatRequest
from backend.models.response import ChatResponse
from backend.retrieval.retriever import Retriever
from backend.storage.metadata_store import MetadataStore

router = APIRouter(prefix="/chat", tags=["Chat"])
metadata_store = MetadataStore()
retriever = Retriever()

@router.post("/", response_model=ChatResponse)
async def chat_with_codebase(request: ChatRequest):
    # Verify repository exists
    try:
        metadata_store.get_repository(request.repository_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Repository not found or not fully indexed yet.")
        
    try:
        response = retriever.answer_question(request.repository_id, request.question)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
