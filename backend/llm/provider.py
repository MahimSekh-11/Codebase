import os
from backend.utils.config import settings
from backend.utils.logger import logger


class LLMProvider:
    """Abstracts away the underlying LLM provider using the new google-genai SDK."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        # Always set the model name — even if no API key is available at startup
        self._model = settings.llm_model or "gemini-2.5-flash"
        self._client = None

        if self.provider == "gemini":
            api_key = settings.llm_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
            if not api_key:
                logger.warning("GEMINI API Key not found at startup. A dynamic key must be passed per request.")
            else:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=api_key)
                    logger.info(f"Gemini client initialized with model: {self._model}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self._client = None
        else:
            raise NotImplementedError(f"LLM Provider '{self.provider}' is not yet supported.")

    def generate(self, prompt: str, api_key: str = None) -> str:
        if self.provider == "gemini":
            client = self._client

            # If a dynamic API key is passed, create a fresh client with it
            if api_key and api_key.strip():
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key.strip())
                    logger.info("Using dynamically provided API key for this request.")
                except Exception as e:
                    logger.error(f"Failed to initialize dynamic Gemini client: {e}")
                    return f"Error: Could not initialize Gemini with the provided API key. Details: {e}"

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
