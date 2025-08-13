import os
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None


class GeminiClient:
    """Minimal Gemini client wrapper.

    Uses GOOGLE_API_KEY from env; if the SDK is missing or key absent,
    generate() will gracefully return a fallback error string.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self._model = None
        if genai and self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                self._model = genai.GenerativeModel(self.model_name)
            except Exception:
                self._model = None

    def available(self) -> bool:
        return bool(self._model)

    def generate(self, prompt: str) -> str:
        if not self._model:
            return "I'm unable to access the fallback LLM right now."
        try:
            resp = self._model.generate_content(prompt)
            return getattr(resp, "text", "") or "I'm sorry, I couldn't generate a response at the moment."
        except Exception:
            return "I'm sorry, I couldn't generate a response at the moment."
