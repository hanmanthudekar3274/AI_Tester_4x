from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract interface all LLM backends must implement."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """Send a prompt and return the completion text."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend can accept requests right now."""
