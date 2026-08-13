import os
import zipfile
import tempfile
import shutil
import uuid
from pathlib import Path
from backend.utils.logger import logger
from backend.utils.config import settings
from backend.utils.security import is_safe_path

class ZipLoader:
    def __init__(self):
        self.base_dir = Path(settings.data_dir) / "repos"
        os.makedirs(self.base_dir, exist_ok=True)
        
    def extract_zip(self, zip_filepath: str, repo_name: str = "upload") -> dict:
        """Extracts a ZIP file safely and returns repository metadata."""
        repo_id = f"zip_{repo_name}_{uuid.uuid4().hex[:8]}"
        repo_path = self.base_dir / repo_id
        os.makedirs(repo_path, exist_ok=True)
        
        logger.info(f"Extracting ZIP into {repo_path}...")
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # Security check against zip slip
                    member_path = os.path.join(repo_path, member)
                    if not is_safe_path(str(repo_path), member_path):
                        logger.warning(f"Skipping unsafe path in ZIP: {member}")
                        continue
                    zip_ref.extract(member, repo_path)
        except Exception as e:
            logger.error(f"Failed to extract ZIP: {e}")
            shutil.rmtree(repo_path, ignore_errors=True)
            raise ValueError(f"Invalid or corrupted ZIP file: {str(e)}")
            
        logger.info(f"Successfully extracted to {repo_path}")
        
        return {
            "repository_id": repo_id,
            "url": "local_zip",
            "local_path": str(repo_path),
            "branch": "main",
            "name": repo_name
        }
