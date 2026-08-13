import os
import re
from urllib.parse import urlparse
from backend.utils.logger import logger

def is_valid_github_url(url: str) -> bool:
    """Validate if the URL is a potentially valid GitHub repository."""
    try:
        parsed = urlparse(url)
        if parsed.netloc != "github.com":
            return False
        
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) != 2:
            return False
            
        return True
    except Exception:
        return False

def is_safe_path(base_dir: str, target_path: str) -> bool:
    """Prevent directory traversal attacks."""
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(target_path)
    return abs_target.startswith(abs_base)

def sanitize_repo_id(url: str) -> str:
    """Generate a safe folder name from a github url."""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    # Replace non-alphanumeric chars with underscores
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', path)
    return safe_name
