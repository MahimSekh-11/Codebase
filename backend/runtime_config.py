# Global in-memory API key store — can be pushed from frontend at runtime
_runtime_api_key: str = ""

def set_runtime_api_key(key: str):
    global _runtime_api_key
    _runtime_api_key = key.strip()

def get_runtime_api_key() -> str:
    return _runtime_api_key
