import os
from pathlib import Path

# Supported source file extensions
SUPPORTED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', 
    '.java', '.c', '.cpp', '.h', '.hpp', 
    '.go', '.rs', '.md', '.json', '.yaml', '.yml',
    '.html', '.css', '.txt', '.php', '.cs', '.sh', 
    '.sql', '.toml', '.xml', '.rst', '.properties'
}

# Directories to ignore
IGNORED_DIRS = {
    '.git', 'node_modules', 'venv', '.env', 'env',
    '__pycache__', 'dist', 'build', 'coverage', 
    'target', 'bin', 'obj'
}

# Binary and media file extensions to ignore
IGNORED_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3', 
    '.zip', '.exe', '.dll', '.so', '.dylib', '.class', 
    '.pdf', '.ico', '.svg', '.lock'
}

def is_source_file(file_path: str) -> bool:
    """Determine if a file should be parsed and indexed."""
    path = Path(file_path)
    
    # Check if inside an ignored directory
    for part in path.parts:
        if part in IGNORED_DIRS:
            return False
            
    # Check exact filename exclusions
    if path.name.startswith('.env') or path.name == 'package-lock.json' or path.name == 'yarn.lock':
        return False
        
    ext = path.suffix.lower()
    
    # Fast path rejections
    if ext in IGNORED_EXTENSIONS:
        return False
        
    # Allowed extensions
    if ext in SUPPORTED_EXTENSIONS:
        return True
        
    # Fallback: ignore unknown files to prevent binary garbage
    return False

def get_language_from_extension(ext: str) -> str:
    """Map file extension to language name."""
    mapping = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.md': 'markdown',
        '.html': 'html',
        '.css': 'css',
        '.txt': 'text',
        '.php': 'php',
        '.cs': 'csharp',
        '.sh': 'shell',
        '.sql': 'sql',
        '.toml': 'toml',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml'
    }
    return mapping.get(ext.lower(), 'text')
