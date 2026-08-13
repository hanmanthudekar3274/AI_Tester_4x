import json
import requests
from .base_llm import BaseLLM


class OllamaLLM(BaseLLM):
    """Ollama local REST client."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
