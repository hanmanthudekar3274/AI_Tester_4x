import os
from .base_llm import BaseLLM
from .ollama_llm import OllamaLLM
from .groq_llm import GroqLLM


class LLMRouter:
    """
    Selects the active LLM backend based on config flags.

    Priority: Groq wins when both are enabled (warns user).
    """

    def __init__(
        self,
        ollama_enabled: bool = False,
        groq_enabled: bool = False,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.2",
        groq_api_key: str = "",
        groq_model: str = "llama3-70b-8192",
    ):
        self.ollama_enabled = ollama_enabled
        self.groq_enabled = groq_enabled
        self._llm: BaseLLM | None = None
        self.warning: str = ""

        if groq_enabled and ollama_enabled:
            self.warning = "Both Ollama and Groq are enabled — Groq takes priority."

        if groq_enabled and groq_api_key:
            self._llm = GroqLLM(api_key=groq_api_key, model=groq_model)
        elif ollama_enabled:
            self._llm = OllamaLLM(base_url=ollama_base_url, model=ollama_model)

    @property
    def active_backend(self) -> str:
        if isinstance(self._llm, GroqLLM):
            return "Groq"
        if isinstance(self._llm, OllamaLLM):
            return "Ollama"
        return "None"

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        if self._llm is None:
            raise RuntimeError(
                "No LLM backend is configured. Enable Ollama or Groq in the sidebar."
            )
        return self._llm.complete(system_prompt, user_prompt, max_tokens)

    @classmethod
    def from_env(cls) -> "LLMRouter":
        return cls(
            ollama_enabled=os.getenv("LLM_OLLAMA_ENABLED", "false").lower() == "true",
            groq_enabled=os.getenv("LLM_GROQ_ENABLED", "false").lower() == "true",
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        )
