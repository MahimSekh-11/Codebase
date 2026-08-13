from fastapi import APIRouter
from pydantic import BaseModel
from backend.runtime_config import set_runtime_api_key, get_runtime_api_key

router = APIRouter(prefix="/settings", tags=["Settings"])

class ApiKeyRequest(BaseModel):
    api_key: str

@router.post("/api-key")
def update_api_key(req: ApiKeyRequest):
    """Frontend calls this to push the user's API key into the backend at runtime."""
    if req.api_key and req.api_key.strip():
        set_runtime_api_key(req.api_key.strip())
        return {"status": "ok", "message": "API key updated in backend memory."}
    return {"status": "error", "message": "Empty API key provided."}

@router.get("/api-key-status")
def get_api_key_status():
    key = get_runtime_api_key()
    return {"has_key": bool(key), "key_preview": f"{key[:6]}..." if key else "not set"}
