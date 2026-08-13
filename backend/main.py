from fastapi import FastAPI
from backend.api import health, repository, chat, settings
from backend.utils.logger import logger
from backend.utils.config import settings as app_settings

app = FastAPI(
    title="CodeBase RAG API",
    description="AI-Powered GitHub Repository Understanding Assistant",
    version="0.1.0",
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(repository.router)
app.include_router(chat.router)
app.include_router(settings.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting CodeBase RAG API...")
    logger.info(f"Using LLM Provider: {settings.llm_provider}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down CodeBase RAG API...")
