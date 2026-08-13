import os
import json
from pathlib import Path
from backend.utils.config import settings
from backend.utils.logger import logger
from backend.models.response import RepositoryStats

class MetadataStore:
    """Simple JSON-based metadata store for the MVP."""
    def __init__(self):
        self.db_path = Path(settings.data_dir) / "metadata.json"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not self.db_path.exists():
            with open(self.db_path, 'w') as f:
                json.dump({}, f)
                
    def _load(self) -> dict:
        with open(self.db_path, 'r') as f:
            return json.load(f)
            
    def _save(self, data: dict):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def save_repository(self, stats: RepositoryStats):
        data = self._load()
        data[stats.repository_id] = stats.model_dump()
        self._save(data)
        logger.info(f"Saved metadata for {stats.repository_id}")
        
    def get_repository(self, repo_id: str) -> RepositoryStats:
        data = self._load()
        if repo_id not in data:
            raise ValueError(f"Repository {repo_id} not found in metadata.")
        return RepositoryStats(**data[repo_id])
        
    def delete_repository(self, repo_id: str):
        data = self._load()
        if repo_id in data:
            del data[repo_id]
            self._save(data)
            logger.info(f"Deleted metadata for {repo_id}")
            
    def list_repositories(self) -> list[RepositoryStats]:
        data = self._load()
        return [RepositoryStats(**repo) for repo in data.values()]
