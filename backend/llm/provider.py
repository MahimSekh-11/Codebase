import os
from backend.utils.config import settings
from backend.utils.logger import logger


class LLMProvider:
    """Abstracts away the underlying LLM provider using the new google-genai SDK."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        if self.provider == "gemini":
            api_key = settings.resolved_api_key
            if not api_key:
                logger.warning("GEMINI API Key not found. LLM generation will fail.")
                self._client = None
            else:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=api_key)
                    # Use gemini-3.5-flash - fast, capable, free-tier available
                    self._model = settings.llm_model or "gemini-3.5-flash"
                    logger.info(f"Gemini client initialized with model: {self._model}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self._client = None
        else:
            raise NotImplementedError(f"LLM Provider '{self.provider}' is not yet supported.")

    def generate(self, prompt: str, api_key: str = None) -> str:
        if self.provider == "gemini":
            from google import genai
            
            client = self._client
            model_name = getattr(self, "_model", "gemini-3.5-flash")

            if api_key:
                # If an API key is provided dynamically, create a temporary client
                try:
                    client = genai.Client(api_key=api_key)
                except Exception as e:
                    logger.error(f"Failed to initialize dynamic Gemini client: {e}")
                    return f"Error: Failed to initialize Gemini client with provided API key: {e}"
            
            if not client:
                return "Error: Gemini API key is missing or invalid. Please set LLM_API_KEY in your .env file or Streamlit secrets."
                
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                logger.error(f"LLM Generation failed: {e}")
                return f"Error from LLM Provider: {str(e)}"
        return ""
