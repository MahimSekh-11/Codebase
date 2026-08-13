import os
from backend.utils.config import settings
from backend.utils.logger import logger


class LLMProvider:
    """Abstracts away the underlying LLM provider using the new google-genai SDK."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        # Always set the model name regardless of whether API key is available at startup
        self._model = settings.llm_model or "gemini-2.5-flash"
        self._client = None

        if self.provider == "gemini":
            api_key = settings.llm_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
            if not api_key:
                logger.warning("No API key at startup — expecting a dynamic key per request.")
            else:
                self._try_init_client(api_key)
        else:
            raise NotImplementedError(f"LLM Provider '{self.provider}' is not yet supported.")

    def _try_init_client(self, api_key: str):
        try:
            from google import genai
            self._client = genai.Client(api_key=api_key.strip())
            logger.info(f"Gemini client initialized with model: {self._model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self._client = None

    def generate(self, prompt: str, api_key: str = None) -> str:
        if self.provider == "gemini":
            # Priority order:
            # 1. Key passed directly in this request
            # 2. Runtime key pushed by frontend via /settings endpoint
            # 3. Client created at startup from env vars
            from backend.runtime_config import get_runtime_api_key
            resolved_key = (api_key or "").strip() or get_runtime_api_key()

            client = self._client
            if resolved_key:
                try:
                    from google import genai
                    client = genai.Client(api_key=resolved_key)
                    logger.info("Using dynamically resolved API key for this request.")
                except Exception as e:
                    logger.error(f"Failed to initialize dynamic Gemini client: {e}")
                    return f"Error: Could not initialize Gemini with provided key. Details: {e}"

            if not client:
                return "Error: Gemini API key is missing or invalid. Please set LLM_API_KEY in your .env file."

            try:
                response = client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                logger.error(f"LLM Generation failed: {e}")
                return f"Error from LLM Provider: {str(e)}"
        return ""
