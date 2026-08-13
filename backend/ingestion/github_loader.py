import os
import shutil
from git import Repo
from pathlib import Path
from backend.utils.logger import logger
from backend.utils.config import settings
from backend.utils.security import sanitize_repo_id

class GithubLoader:
    def __init__(self):
        self.base_dir = Path(settings.data_dir) / "repos"
        os.makedirs(self.base_dir, exist_ok=True)
        
    def clone_repository(self, url: str) -> dict:
        """Clones a GitHub repository and returns its metadata."""
        repo_id = sanitize_repo_id(url)
        repo_path = self.base_dir / repo_id
        
        # If exists, clean it up for fresh clone (in MVP, we just overwrite)
        if repo_path.exists():
            logger.info(f"Removing existing repo at {repo_path}")
            shutil.rmtree(repo_path, ignore_errors=True)
            
        logger.info(f"Cloning {url} into {repo_path}...")
        try:
            repo = Repo.clone_from(url, repo_path, depth=1) # shallow clone for speed
            default_branch = repo.active_branch.name
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise ValueError(f"Failed to clone repository: {str(e)}")
            
        logger.info(f"Successfully cloned {url} (branch: {default_branch})")
        
        return {
            "repository_id": repo_id,
            "url": url,
            "local_path": str(repo_path),
            "branch": default_branch,
            "name": repo_id.split('_')[-1]
        }
