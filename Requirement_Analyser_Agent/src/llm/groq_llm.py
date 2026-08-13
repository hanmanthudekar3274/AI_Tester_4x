from groq import Groq
from .base_llm import BaseLLM


class GroqLLM(BaseLLM):
    """Groq cloud inference client."""

    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model

    def is_available(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content
