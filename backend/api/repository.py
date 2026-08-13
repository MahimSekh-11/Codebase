import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from backend.models.request import IndexRepositoryRequest
from backend.models.response import IndexRepositoryResponse, RepositoryStats
from backend.utils.security import is_valid_github_url
from backend.ingestion.github_loader import GithubLoader
from backend.ingestion.zip_loader import ZipLoader
from backend.ingestion.file_filter import is_source_file, get_language_from_extension
from backend.ingestion.parser import CodeParser
from backend.ingestion.chunker import Chunker
from backend.storage.metadata_store import MetadataStore
from backend.retrieval.vector_store import VectorStore
from backend.utils.logger import logger
from backend.utils.config import settings

router = APIRouter(prefix="/repository", tags=["Repository"])
metadata_store = MetadataStore()

def process_repository(repo_path: str, repo_id: str, repo_name: str):
    """Core function to parse, chunk, and embed a repository."""
    logger.info(f"Starting processing for {repo_id} at {repo_path}")
    parser = CodeParser()
    chunker = Chunker()
    vector_store = VectorStore(repo_id)
    
    file_count = 0
    chunk_count = 0
    languages = {}
    total_size = 0
    
    all_chunks = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Simple size limit per file (e.g., skip files > 1MB)
            if os.path.getsize(file_path) > 1024 * 1024:
                continue
                
            if is_source_file(file_path):
                file_count += 1
                total_size += os.path.getsize(file_path)
                ext = Path(file_path).suffix
                lang = get_language_from_extension(ext)
                languages[lang] = languages.get(lang, 0) + 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Parse and Chunk
                    parsed_blocks = parser.parse_file(content, lang, rel_path)
                    chunks = chunker.chunk_parsed_data(parsed_blocks, repo_id, rel_path, lang)
                    
                    all_chunks.extend(chunks)
                    chunk_count += len(chunks)
                except UnicodeDecodeError:
                    logger.warning(f"Skipping binary/unreadable file: {file_path}")
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    
    # Embed and Store
    vector_store.add_chunks(all_chunks)
    
    # Save Metadata
    stats = RepositoryStats(
        repository_id=repo_id,
        repository_name=repo_name,
        file_count=file_count,
        chunk_count=chunk_count,
        languages=languages,
        size_kb=round(total_size / 1024, 2)
    )
    metadata_store.save_repository(stats)
    logger.info(f"Finished indexing {repo_id}. {file_count} files, {chunk_count} chunks.")

@router.post("/index", response_model=IndexRepositoryResponse)
async def index_github_repo(request: IndexRepositoryRequest, background_tasks: BackgroundTasks):
    url = str(request.repo_url)
    if not is_valid_github_url(url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
    loader = GithubLoader()
    try:
        repo_data = loader.clone_repository(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    repo_id = repo_data["repository_id"]
    
    # Run processing in background
    background_tasks.add_task(process_repository, repo_data["local_path"], repo_id, repo_data["name"])
    
    return IndexRepositoryResponse(
        repository_id=repo_id,
        repository_name=repo_data["name"],
        file_count=0,
        chunk_count=0,
        status="indexing_started"
    )

@router.post("/upload", response_model=IndexRepositoryResponse)
async def upload_zip_repo(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Must be a ZIP file")
        
    loader = ZipLoader()
    
    # Save uploaded file temporarily
    temp_zip = Path(settings.data_dir) / f"temp_{file.filename}"
    try:
        with open(temp_zip, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
        repo_data = loader.extract_zip(str(temp_zip), file.filename.replace('.zip', ''))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_zip.exists():
            os.remove(temp_zip)
            
    repo_id = repo_data["repository_id"]
    background_tasks.add_task(process_repository, repo_data["local_path"], repo_id, repo_data["name"])
    
    return IndexRepositoryResponse(
        repository_id=repo_id,
        repository_name=repo_data["name"],
        file_count=0,
        chunk_count=0,
        status="indexing_started"
    )

@router.get("/{repository_id}/stats", response_model=RepositoryStats)
async def get_stats(repository_id: str):
    try:
        return metadata_store.get_repository(repository_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=list[RepositoryStats])
async def list_repositories():
    return metadata_store.list_repositories()

@router.delete("/{repository_id}")
async def delete_repository(repository_id: str):
    try:
        metadata_store.delete_repository(repository_id)
        VectorStore.delete_index(repository_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
