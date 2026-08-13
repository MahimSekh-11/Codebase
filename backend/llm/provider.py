import os
from backend.utils.config import settings
from backend.utils.logger import logger


class LLMProvider:
    """Abstracts away the underlying LLM provider using the new google-genai SDK."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        if self.provider == "gemini":
            api_key = settings.llm_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
            if not api_key:
                logger.warning("GEMINI API Key not found. LLM generation will fail.")
                self._client = None
            else:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=api_key)
                    # Use gemini-flash-latest to ensure an active, working flash model is selected
                    self._model = settings.llm_model or "gemini-flash-latest"
                    logger.info(f"Gemini client initialized with model: {self._model}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self._client = None
        else:
            raise NotImplementedError(f"LLM Provider '{self.provider}' is not yet supported.")

    def generate(self, prompt: str) -> str:
        if self.provider == "gemini":
            if not self._client:
                return "Error: Gemini API key is missing or invalid. Please set LLM_API_KEY in your .env file."
            try:
                from google import genai
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                logger.error(f"LLM Generation failed: {e}")
                return f"Error from LLM Provider: {str(e)}"
        return ""
